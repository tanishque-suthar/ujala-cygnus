# Agent Instructions — Backend

## Tech
FastAPI, Python. Runs on `localhost:8000`. Async SQLAlchemy 2.0 (`aiosqlite`), Alembic for migrations, httpx for model server calls, Tesseract OCR (`pytesseract`, `pdf2image`, `Pillow`).
*Note: Requires system-level dependencies `tesseract-ocr` and `poppler-utils` (`sudo apt install tesseract-ocr poppler-utils`).*

## Responsibility
Application layer between Frontend and Model Server. Receives image/PDF uploads with patient data, forwards X-ray scans to Model Server for inference or runs OCR on medical reports, persists results and patient demographics in SQLite, and returns formatted responses.

## Key Config (env vars, see `app/config.py`)
- `MODEL_SERVER_URL` — default `http://localhost:8001`
- `DB_PATH` — default `database/cygnus.db` (project root)
- `UPLOADS_DIR` — default `database/uploads` (images to `{UPLOADS_DIR}/images/`, heatmaps to `{UPLOADS_DIR}/heatmaps/`, reports to `{UPLOADS_DIR}/reports/` with `temp/` subfolder)
- `reports_dir` — `Path(uploads_dir) / "reports"` property

## File Structure (package `app/`)

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app + lifespan (dirs, migrations, model client, active model name, OCR service check) |
| `app/config.py` | Pydantic settings (`model_server_url`, `db_path`, `uploads_dir`, `reports_dir`) |
| `app/database.py` | Async engine, session factory, `get_session` dependency |
| `app/models/` | SQLAlchemy ORM: `patient.py`, `document.py`, `scan_result.py`, `report_result.py` |
| `app/schemas/` | Pydantic responses: `models.py` (Screen/Health/Error), `patient.py`, `document.py`, `report.py` |
| `app/routers/` | Endpoints: `screen.py`, `health.py`, `patients.py`, `documents.py`, `reports.py` |
| `app/services/model_client.py` | httpx client for Model Server (`ModelClient`, `ModelServerError`) |
| `app/services/ocr_service.py` | Tesseract OCR wrapper: preprocessing, `--psm 6`, PDF text-layer fallback (`pdftotext`), 300 DPI rasterization, mean word confidence (`OCRService`) |
| `app/services/field_extractor.py` | Pure-text typed field extraction: header fields (patient/date/doctor/facility), report type inference, curated lab-panel ontology (`extract`) — only known tests are captured, no generic key:value noise |
| `alembic/` + `alembic.ini` | DB migrations (run automatically at startup) |
| `tests/` | pytest suite (httpx `ASGITransport`, `asyncio_mode = "auto"`) — includes `/screen`, `/reports/upload`, `/patients`, `/health`, extractor unit tests, and OCR service tests |

## Database & Migrations
- Alembic migrations are applied automatically at startup (`command.upgrade(cfg, "head")` in lifespan) — never hand-create tables.
- Existing migrations: `e2f29abded28` (initial schema), `3a1b2c3d4e5f` (dropped `priority` column from `scan_results`), patient demographics migration, `report_results` table migration.

## Active model name
`model_used` is **not** a static config value. At startup, the backend calls the model server `GET /health` and reads `model_backend` from the response, storing it on `app.state.active_model_name`. It is **refreshed before every `/screen` predict** (a health ping is done first) so `model_used` always reflects what the model server is actually running.

If the model server is unreachable, `app.state.active_model_name` stays `"unknown"` and the `/screen` endpoint returns `502`.

## Endpoints

### `POST /screen`
**Request:** `multipart/form-data` — `file` (image), `patient_name` (required), `patient_id` (optional).

**Behavior:**
1. Validate file present → `400` if missing
2. Validate file type (`image/jpeg` or `image/png`) → `400` if invalid
3. Validate `patient_name` is non-empty → `400` if blank
4. Validate file size ≤ 10 MB → `413` if exceeded
5. Ping model server `/health` and refresh `app.state.active_model_name`
6. Forward to Model Server `POST /predict` (30s timeout) → `502` on failure (with server error detail if available)
7. Validate model server response contains required keys (`prediction`, `confidence`, `heatmap_base64`) → `502` if malformed
8. Save image to `database/uploads/images/{doc_id}.{ext}` and decode heatmap base64 to `database/uploads/heatmaps/{scan_id}.png`
9. Create/link Patient, Document (`document_type="xray"`), ScanResult records in SQLite
   - If `patient_id` provided but not found → `404` (files cleaned up)
   - If `patient_id` not provided → create new Patient
   - Any DB failure → `500` (files cleaned up)
10. Pass through `pathology_scores` and `op_threshs` from Model Server response unchanged
11. Return ScreenResponse

**Response (200):**
```json
{
  "prediction": "enlarged cardiomediastinum",
  "confidence": 0.62,
  "model_used": "biomedclip",
  "heatmap_base64": "...",
  "pathology_scores": {
    "enlarged cardiomediastinum": 0.6241,
    "cardiomegaly": 0.5179,
    "pneumonia": 0.1077,
    "lung opacity": 0.215,
    "support device": 0.236
  },
  "op_threshs": {
    "enlarged cardiomediastinum": 0.5,
    "cardiomegaly": 0.55,
    "pneumonia": 0.3,
    "lung opacity": 0.45,
    "support device": 0.4
  },
  "timestamp": "2026-08-08T10:00:00Z",
  "document_id": "uuid",
  "patient_id": "uuid",
  "patient_name": "Jane Doe"
}
```

### `POST /reports/upload`
**Request:** `multipart/form-data` — `file` (JPEG, PNG, or PDF, ≤ 20 MB).

**Behavior:**
1. Validate file present & mimetype (`image/jpeg`, `image/png`, `application/pdf`) → `400` if invalid
2. Validate file size ≤ 20 MB → `413` if exceeded
3. Save file temporarily to `database/uploads/reports/temp/{temp_id}.{ext}`
4. Run OCR via `OCRService` — PDFs with an embedded text layer use `pdftotext` (confidence 100.0); otherwise pages are rasterized at 300 DPI, preprocessed (grayscale, upscale, autocontrast, unsharp), and OCR'd with `--psm 6`. Returns text, page count, and mean word confidence
5. Run typed extraction via `field_extractor.extract(raw_text)` → patient name, ISO-8601 report date, doctor, facility, inferred report type (`lab_panel`/`discharge_summary`/`referral_letter`/`other`), and lab-panel fields (only canonical tests with matching units)
6. Return `OCRUploadResponse` containing `temp_id`, `filename`, extracted fields, raw text, `page_count`, and `ocr_confidence`

### `POST /reports/confirm`
**Request:** JSON body `ReportConfirmRequest` — `temp_id`, `patient_name`, optional `patient_id`, `report_type` (`lab_panel`, `discharge_summary`, `referral_letter`, `other`), optional `report_date`, `doctor_name`, `facility_name`, `extracted_fields` dict, `raw_text`, optional patient demographic fields (`patient_age`, `patient_sex`, `patient_dob`, `patient_contact`, `patient_mrn`, `referring_physician`).

**Behavior:**
1. Validate temp file exists for `temp_id` → `404` if missing
2. Move file from temp folder to permanent storage `database/uploads/reports/{document_id}.{ext}`
3. Create new `Patient` (or link to existing `patient_id`) with provided demographics
4. Create `Document` record (`document_type="report"`)
5. Create `ReportResult` record linked 1:1 to Document
6. Return `ReportConfirmResponse`

### `GET /reports/{document_id}/file`
Stream original uploaded report file (image or PDF) from disk via `FileResponse`. `404` if row or file is missing.

### `GET /health`
Pings Model Server `/health` (5s timeout) and returns `{"status": "ok", "model_server_reachable": bool}` — `false` when the model server is down, never an error.

### `GET /patients`
List all patients with `record_count` (number of documents), ordered newest first.

### `GET /patients/stats`
Returns `{"total_patients": int, "total_documents": int}`.

### `POST /patients`
**Body:** `{"name": string, "age": int|null, "sex": string|null, "date_of_birth": string|null, "contact": string|null, "mrn": string|null, "referring_physician": string|null, "medical_history": string|null}` → `201` with created patient.

### `GET /patients/{patient_id}`
Patient details (including expanded demographic fields) with nested documents, each including its scan result or report result (when present). `404` if not found.

### `GET /patients/{patient_id}/documents`
All documents for a patient with nested scan results and report results, newest first.

### `GET /documents/{document_id}`
Single document with nested scan result or report result. `404` if not found.

### `GET /image/{document_id}` & `GET /heatmap/{scan_result_id}`
Stream original image / heatmap PNG from disk via `FileResponse` (media type inferred from extension). `404` if the row or file is missing.

## Database Schema
- **Patient** — `id`, `name`, `age` (nullable int), `sex` (nullable str), `date_of_birth` (nullable str), `contact` (nullable str), `mrn` (nullable unique str), `referring_physician` (nullable str), `medical_history` (nullable text), `created_at` (`documents` cascade-deletes)
- **Document** — `id`, `patient_id` (FK), `document_type` (`"xray"` or `"report"`), `file_path`, `filename`, `uploaded_at`; optional 1:1 `scan_result`, optional 1:1 `report_result`
- **ScanResult** — `id`, `document_id` (FK, unique), `prediction`, `confidence`, `model_used`, `pathology_scores` (JSON), `op_threshs` (JSON), `heatmap_path` (nullable), `analyzed_at`
- **ReportResult** — `id`, `document_id` (FK, unique), `report_type` (`lab_panel`, `discharge_summary`, `referral_letter`, `other`), `report_date` (nullable str), `raw_text` (nullable text), `extracted_fields` (nullable JSON), `doctor_name` (nullable str), `facility_name` (nullable str), `processed_at`

## Rules
- Never perform inference or preprocessing — always delegate to Model Server
- CORS: allow `localhost:3000` only
- Timeout on Model Server: 30s → `502`; health ping timeout: 5s
- `pathology_scores` and `op_threshs` are passed through from Model Server response unchanged
- Never create tables manually — add an Alembic migration and let startup apply it
- Run tests with `pytest` in `backend/` (includes `/screen`, `/reports`, `/patients`, and `/health` tests)
- OCR extraction regression: `evaluation/eval_ocr.py` scores `field_extractor` against `evaluation/ocr_test_set/` (`.txt` sample + `.expected.json` per case) — run it after touching extraction logic