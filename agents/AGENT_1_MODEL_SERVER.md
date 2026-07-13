# Agent Instructions — Model Server

## Tech
FastAPI, Python. Runs on `localhost:8001`.

## Responsibility
Pure inference microservice. Loads a trained PyTorch model and serves
predictions on chest X-ray images. No business logic, no priority
calculation, no auth. Just: image in → prediction + heatmap out.

## Startup behavior
- Load the model weights (`.pth`) into memory **once at server startup**,
  not per-request. Keep the model in a module-level/global variable.
- Model architecture (DenseNet121 / ViT / BiomedCLIP — TBD which one is
  final) must be defined in code matching the saved `state_dict`.
- Load with `model.load_state_dict(torch.load(path))`, then `model.eval()`.

## Preprocessing
- Implement one preprocessing function: resize → normalize → tensor.
- Must exactly match the preprocessing used during training (same resize
  dimensions, same normalization mean/std, same grayscale/RGB handling).
- This function will be provided/confirmed separately — do not invent
  normalization values; use placeholders clearly marked `# CONFIRM: match
  training preprocessing` until given the real values.

## Endpoint

### `POST /predict`

**Request:** `multipart/form-data`
- `file`: image file (jpeg/png)

**Response:** `200 OK`, JSON:
```json
{
  "prediction": "pneumonia",
  "confidence": 0.91,
  "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

Field rules:
- `prediction`: string, either `"normal"` or `"pneumonia"` (lowercase, exact)
- `confidence`: float, 0–1, confidence of the predicted class (not
  necessarily the positive class)
- `heatmap_base64`: PNG image, base64-encoded string (no data URI prefix),
  showing Grad-CAM (CNN) or attention rollout (ViT/BiomedCLIP) overlay on
  the original image

**Error responses:**
- `400` if uploaded file is not a valid image or wrong type
- `500` with JSON `{"error": "<message>"}` if inference fails

## Health check endpoint

### `GET /health`
Response: `200 OK`, `{"status": "ok", "model_loaded": true}`

## Explicit rules
- Do not add authentication, database, logging beyond basic error logging,
  or priority/risk logic — that belongs in the Backend service, not here.
- Do not hardcode file paths outside a config/env variable for the model
  weights path.
- CORS: allow requests from Backend only (`localhost:8000`) — not from the
  Frontend directly.
