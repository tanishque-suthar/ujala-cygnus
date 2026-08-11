# Agent Instructions — Backend

## Tech
FastAPI, Python. Runs on `localhost:8000`. Async SQLAlchemy 2.0 (`aiosqlite`), Alembic for migrations, httpx for model server calls.

## Responsibility
Application layer between Frontend and Model Server. Receives image uploads with patient data, forwards to Model Server for inference, persists results in SQLite, and returns a formatted response.

## Key Config (env vars, see `app/config.py`)
- `MODEL_SERVER_URL` — default `http://localhost:8001`
- `DB_PATH` — default `database/cygnus.db` (project root)
- `UPLOADS_DIR` — default `database/uploads` (images to `{UPLOADS_DIR}/images/`, heatmaps to `{UPLOADS_DIR}/heatmaps/`)

## File Structure (package `app/`)

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app + lifespan (dirs, migrations, model client, active model name) |
| `app/config.py` | Pydantic settings (`model_server_url`, `db_path`, `uploads_dir`) |
| `app/database.py` | Async engine, session factory, `get_session` dependency |
| `app/models/` | SQLAlchemy ORM: `patient.py`, `document.py`, `scan_result.py` |
| `app/schemas/` | Pydantic responses: `models.py` (Screen/Health/Error), `patient.py`, `document.py` |
| `app/routers/` | Endpoints: `screen.py`, `health.py`, `patients.py`, `documents.py` |
| `app/services/model_client.py` | httpx client for Model Server (`ModelClient`, `ModelServerError`) |
| `alembic/` + `alembic.ini` | DB migrations (run automatically at startup) |
| `tests/` | pytest suite (httpx `ASGITransport`, `asyncio_mode = "auto"`) |

## Database & Migrations
- Alembic migrations are applied automatically at startup (`command.upgrade(cfg, "head")` in lifespan) — never hand-create tables.
- Existing migrations: `e2f29abded28` (initial schema), `3a1b2c3d4e5f` (dropped `priority` column from `scan_results`).

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
    "support device": 0.236,
    ...
  },
  "op_threshs": {
    "enlarged cardiomediastinum": 0.5,
    "cardiomegaly": 0.55,
    "pneumonia": 0.3,
    "lung opacity": 0.45,
    "support device": 0.4,
    ...
  },
  "timestamp": "2026-08-08T10:00:00Z",
  "document_id": "uuid",
  "patient_id": "uuid",
  "patient_name": "Jane Doe"
}
```

### `GET /health`
Pings Model Server `/health` (5s timeout) and returns `{"status": "ok", "model_server_reachable": bool}` — `false` when the model server is down, never an error.

### `GET /patients`
List all patients with `record_count` (number of documents), ordered newest first.

### `GET /patients/stats`
Returns `{"total_patients": int, "total_documents": int}`.

### `POST /patients`
**Body:** `{"name": string}` → `201` with created patient (`id`, `name`, `created_at`).

### `GET /patients/{patient_id}`
Patient details with nested documents, each including its scan result (when present). `404` if not found.

### `GET /patients/{patient_id}/documents`
All documents for a patient with nested scan results, newest first.

### `GET /documents/{document_id}`
Single document with nested scan result. `404` if not found.

### `GET /image/{document_id}` & `GET /heatmap/{scan_result_id}`
Stream original image / heatmap PNG from disk via `FileResponse` (media type inferred from extension). `404` if the row or file is missing.

## Database Schema
- **Patient** — `id`, `name`, `created_at` (`documents` cascade-deletes)
- **Document** — `id`, `patient_id` (FK), `document_type`, `file_path`, `filename`, `uploaded_at`; one-to-one `scan_result`
- **ScanResult** — `id`, `document_id` (FK, unique), `prediction`, `confidence`, `model_used`, `pathology_scores` (JSON), `op_threshs` (JSON), `heatmap_path` (nullable), `analyzed_at`

## Rules
- Never perform inference or preprocessing — always delegate to Model Server
- CORS: allow `localhost:3000` only
- Timeout on Model Server: 30s → `502`; health ping timeout: 5s
- `pathology_scores` and `op_threshs` are passed through from Model Server response unchanged
- Never create tables manually — add an Alembic migration and let startup apply it
- Run tests with `pytest` in `backend/` (currently cover `/screen` validation + model-server-unreachable and `/health` behavior)