# Agent Instructions — Backend

## Tech
FastAPI, Python. Runs on `localhost:8000`.

## Responsibility
Application layer between Frontend and Model Server. Receives image
uploads, forwards to Model Server for inference, applies business logic
(priority mapping), and returns a formatted response. Owns validation.

## Endpoint

### `POST /screen`

**Request:** `multipart/form-data`
- `file`: image file (jpeg/png)

**Behavior:**
1. Validate the uploaded file:
   - Must be `image/jpeg` or `image/png`
   - Max size: 10 MB (reject larger with `413`)
   - If invalid, return `400` with `{"error": "<reason>"}`
2. Forward the file to Model Server at `http://localhost:8001/predict`
   (use env var `MODEL_SERVER_URL`, default `http://localhost:8001`, so
   this can be changed later without code changes)
3. If Model Server returns an error or is unreachable, return `502` with
   `{"error": "Model server unavailable"}`
4. On success, map `confidence` to a `priority` field:
   - `confidence >= 0.85` → `"high"`
   - `0.6 <= confidence < 0.85` → `"moderate"`
   - `confidence < 0.6` → `"low"`
   (Only apply priority mapping when `prediction == "pneumonia"`. If
   `prediction == "normal"`, set `priority` to `"low"` regardless of
   confidence.)
5. Return combined response.

**Response:** `200 OK`, JSON:
```json
{
  "prediction": "pneumonia",
  "confidence": 0.91,
  "priority": "high",
  "model_used": "densenet121",
  "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "timestamp": "2026-07-13T10:00:00Z"
}
```

Field rules:
- `prediction`, `confidence`, `heatmap_base64`: passed through unchanged
  from Model Server response
- `priority`: string, one of `"low"`, `"moderate"`, `"high"` — computed
  here, not by Model Server
- `model_used`: string, hardcoded/config value naming which model is
  currently deployed on the Model Server (e.g. `"densenet121"`) — set via
  env var `ACTIVE_MODEL_NAME`
- `timestamp`: ISO 8601 UTC timestamp of when the request was processed

## Health check endpoint

### `GET /health`
Response: `200 OK`, `{"status": "ok", "model_server_reachable": true}`
(should actually ping Model Server's `/health` to determine the second
field)

## Explicit rules
- Do not perform inference or preprocessing here — always delegate to
  Model Server.
- Do not add a database or persistence layer unless explicitly asked later.
- CORS: allow requests from Frontend only (`localhost:3000`).
- Timeout on the Model Server call: 30 seconds, then treat as failure (`502`).

## Database & Storage Decisions

### SQLite & SQLAlchemy ORM
- Database path configured absolutely from project root to `database/cygnus.db` using settings configured in `app/config.py`.
- Managed via SQLAlchemy ORM models: `Patient`, `Document`, and `ScanResult`.
- Migration history handled via **Alembic**; run migrations via async engine setup (`alembic/env.py`).

### File Storage
- Uploaded original files stored on disk: `database/uploads/images/{document_id}.{ext}`.
- Model heatmaps stored on disk: `database/uploads/heatmaps/{scan_result_id}.png`.
- DB records reference relative pathways, and endpoints stream them to the frontend.

### Schema Relationships
- `Patient` (1) ↔ (N) `Document` (has UUID, name, created_at timestamp).
- `Document` (1) ↔ (0..1) `ScanResult` (contains prediction, confidence, computed priority, model used, and heatmap path).
- Discriminator `document_type` (e.g. `"xray"`) dynamically tags documents without schema constraints.

### Updated Endpoint Actions

#### `POST /screen`
- Accepts `file` (UploadFile), `patient_name` (Form parameter), and optional `patient_id` (Form parameter).
- Automatically links to patient if `patient_id` exists, or instantiates a new `Patient` record.
- Writes files to disk, maps DB relationships, saves `ScanResult`, and returns `ScreenResponse` (extended with `document_id`, `patient_id`, and `patient_name`).

#### `GET /patients` & `GET /patients/stats`
- Lists all patients with `record_count`.
- Returns stats containing total counts of patients and documents.

#### `GET /patients/{patient_id}`
- Returns nested patient details + document list with their respective scan results.

#### `GET /image/{document_id}` & `GET /heatmap/{scan_result_id}`
- Files are read from storage and streamed via `FileResponse` with correct MIME types.

