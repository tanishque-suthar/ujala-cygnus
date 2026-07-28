# Agent Instructions — Model Server

## Tech
FastAPI, Python. Runs on `localhost:8001`.

## Responsibility
Loads a pretrained chest X-ray classification model, runs inference on uploaded images, and returns a prediction with an explainability heatmap. Leaf service — calls nothing upstream.

## Model

### Architecture
TorchXRayVision's `DenseNet121` with `densenet121-res224-all` weights. This is a multi-label classifier trained across multiple chest X-ray datasets (NIH, CheXpert, MIMIC-CXR, PadChest, etc.) covering 18 pathologies:

Atelectasis, Consolidation, Infiltration, Pneumothorax, Edema, Emphysema, Fibrosis, Effusion, **Pneumonia**, Pleural_Thickening, Cardiomegaly, Nodule, Mass, Hernia, Lung Lesion, Fracture, Lung Opacity, Enlarged Cardiomediastinum

Weights are auto-downloaded by torchxrayvision to `~/.torchxrayvision/` on first load.

### Preprocessing Pipeline
1. Convert input to **grayscale** (PIL `"L"` mode)
2. Normalize pixel values from [0, 255] to [-1024, 1024] via `xrv.datasets.normalize(img, 255)`
3. Add channel dimension → shape `(1, H, W)`
4. Center crop via `xrv.datasets.XRayCenterCrop()`
5. Resize to 224×224 via `xrv.datasets.XRayResizer(224)`
6. Convert to tensor, unsqueeze batch dim → final shape `(1, 1, 224, 224)`

### Inference Flow
1. Forward pass through DenseNet → raw logits of shape `(1, 18)`
2. Apply `torch.sigmoid` to get per-pathology probabilities
3. Build `pathology_scores` dict from all 18 sigmoid values
4. Build `op_threshs` dict from `model.op_threshs` (pre-calibrated operating thresholds shipped with the model weights)
5. Find all pathologies (excluding `"Lung Opacity"`) where `probability >= threshold`
6. If any qualify → pick the highest-scoring one as the prediction; its score becomes `confidence`
7. If none qualify → `prediction = "normal"`, `confidence = 0.0`
8. All 18 sigmoid scores and all 18 thresholds are returned in the response

### Explainability (Grad-CAM)
Uses `captum.attr.LayerGradCam` targeting `model.features[-1]` (the final DenseBlock).

1. Clone input tensor with `requires_grad_(True)`
2. Determine the **target class index**:
   - If a pathology exceeded its threshold → target is that winning pathology's index
   - If none exceeded (prediction is `"normal"`) → target is the overall highest-scoring pathology (any pathology, including `"Lung Opacity"`), so a meaningful heatmap is always generated
3. Compute Grad-CAM attribution for the target index
4. ReLU + normalize the activation map to [0, 1]
5. Resize through 224×224 first (matching the model's feature space), then to the cropped image dimensions (bicubic interpolation)
6. Apply `inferno` colormap from matplotlib
7. Blend with original RGB image using intensity-scaled alpha (max 75% — hotter regions show more heatmap, cooler regions show more original)
8. Encode overlay as PNG → base64 string (no `data:` URI prefix)

## File Structure

| File | Purpose |
|---|---|
| `inference.py` | Model loading, preprocessing, Grad-CAM, prediction logic |
| `main.py` | FastAPI app, lifespan, endpoints, CORS |
| `app_config.py` | Pydantic settings (`model_weights` field, overridable via `MODEL_WEIGHTS` env var) |
| `requirements.txt` | Python dependencies |

Note: the inference module is named `inference.py` (not `model.py`) to avoid shadowing torchxrayvision's internal `model` package which breaks its `jfhealthcare` baseline import chain.
Note: the config module is named `app_config.py` (not `config.py`) to avoid shadowing torchxrayvision's internal `config` package.

## Endpoints

### `GET /health`
Returns `{"status": "ok", "model_loaded": true}` or `503` if model failed to load.

### `POST /predict`
**Request:** `multipart/form-data` with `file` (JPEG or PNG).

**Response (200):**
```json
{
  "prediction": "Consolidation",
  "confidence": 0.8721,
  "heatmap_base64": "iVBORw0KGgo...",
  "pathology_scores": {
    "Atelectasis": 0.1234,
    "Consolidation": 0.8721,
    "Pneumonia": 0.0542,
    "Lung Opacity": 0.3123,
    ...
  },
  "op_threshs": {
    "Atelectasis": 0.0742,
    "Consolidation": 0.0383,
    "Pneumonia": 0.0568,
    "Lung Opacity": 0.2020,
    ...
  }
}
```

When no pathology exceeds its threshold:
```json
{
  "prediction": "normal",
  "confidence": 0.0,
  "heatmap_base64": "iVBORw0KGgo...",
  "pathology_scores": { ... },
  "op_threshs": { ... }
}
```
The `prediction` field is `"normal"` and `confidence` is `0.0`. A heatmap is still generated against the overall highest-scoring pathology.

**Errors:**
- `400` — invalid file type, unreadable image, or oversized file
- `500` — inference failure with `{"error": "<detail>"}`

## Dependencies
`torch`, `torchvision`, `torchxrayvision`, `captum`, `scikit-image`, `fastapi`, `uvicorn`, `Pillow`, `numpy`, `matplotlib`
