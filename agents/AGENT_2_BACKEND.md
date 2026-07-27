# Agent Instructions — Backend

## Tech
FastAPI, Python. Runs on `localhost:8000`.

## Responsibility
Application layer between Frontend and Model Server. Receives image uploads with patient data, forwards to Model Server for inference, persists results in SQLite, and returns a formatted response.

## Key Config (env vars)
- `MODEL_SERVER_URL` — default `http://localhost:8001`
- `ACTIVE_MODEL_NAME` — default `densenet121`
- DB at `database/cygnus.db`, uploads at `database/uploads/`

## Endpoints

### `POST /screen`
**Request:** `multipart/form-data` — `file` (image), `patient_name` (required), `patient_id` (optional).

**Behavior:**
1. Validate file type (`image/jpeg` or `image/png`) → `400` if invalid
2. Validate file size ≤ 10 MB → `413` if exceeded
3. Forward to Model Server `POST /predict` (30s timeout) → `502` on failure
4. Save image to `database/uploads/images/{doc_id}.{ext}`
5. Decode heatmap base64 and save to `database/uploads/heatmaps/{scan_id}.png`
6. Create/link Patient, Document, ScanResult records in SQLite
7. Pass through `op_threshs` from Model Server response unchanged
8. Return ScreenResponse

**Response (200):**
```json
{
  "prediction": "Consolidation",
  "confidence": 0.87,
  "model_used": "densenet121",
  "heatmap_base64": "...",
  "pathology_scores": {"Consolidation": 0.87, "Atelectasis": 0.12, "Lung Opacity": 0.31, ...},
  "op_threshs": {"Atelectasis": 0.0742, "Consolidation": 0.0383, "Pneumonia": 0.0568, "Lung Opacity": 0.2020, ...},
  "timestamp": "2026-07-26T10:00:00Z",
  "document_id": "uuid",
  "patient_id": "uuid",
  "patient_name": "Jane Doe"
}
```

### `GET /health`
Pings Model Server `/health` and returns `{"status": "ok", "model_server_reachable": bool}`.

### `GET /patients` & `GET /patients/stats`
List all patients with record counts. Stats returns totals.

### `GET /patients/{patient_id}`
Patient details with nested documents and scan results.

### `GET /image/{document_id}` & `GET /heatmap/{scan_result_id}`
Stream original image / heatmap PNG from disk via `FileResponse`.

## Database Schema
- **Patient** — `id`, `name`, `created_at`
- **Document** — `id`, `patient_id` (FK), `document_type`, `file_path`, `filename`, `created_at`
- **ScanResult** — `id`, `document_id` (FK, unique), `prediction`, `confidence`, `model_used`, `heatmap_path`, `analyzed_at`

## Rules
- Never perform inference or preprocessing — always delegate to Model Server
- CORS: allow `localhost:3000` only
- Timeout on Model Server: 30s → `502`
- `pathology_scores` and `op_threshs` are passed through from Model Server response unchanged
