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
- Timeout on the Model Server call: 30 seconds, then treat as failure
  (`502`).
