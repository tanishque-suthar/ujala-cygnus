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
3. Extract Pneumonia probability at `model.pathologies.index("Pneumonia")`
4. Compare against `model.op_threshs[pneumonia_idx]` (pre-calibrated operating threshold shipped with the model weights) to decide `"pneumonia"` vs `"normal"`
5. Confidence = `pneumonia_prob` if pneumonia, else `1.0 - pneumonia_prob`
6. All 18 sigmoid scores are returned as `pathology_scores`

### Explainability (Grad-CAM)
Uses `captum.attr.LayerGradCam` targeting `model.features[-1]` (the final DenseBlock).

1. Clone input tensor with `requires_grad_(True)`
2. Compute Grad-CAM attribution for the Pneumonia class index
3. ReLU + normalize the activation map to [0, 1]
4. Resize to original image dimensions (bicubic interpolation)
5. Apply `inferno` colormap from matplotlib
6. Blend with original RGB image using intensity-scaled alpha (max 75% — hotter regions show more heatmap, cooler regions show more original)
7. Encode overlay as PNG → base64 string (no `data:` URI prefix)

## File Structure

| File | Purpose |
|---|---|
| `inference.py` | Model loading, preprocessing, Grad-CAM, prediction logic |
| `main.py` | FastAPI app, lifespan, endpoints, CORS |
| `config.py` | Pydantic settings (currently minimal, extensible via env vars) |
| `requirements.txt` | Python dependencies |

Note: the inference module is named `inference.py` (not `model.py`) to avoid shadowing torchxrayvision's internal `model` package which breaks its `jfhealthcare` baseline import chain.

## Endpoints

### `GET /health`
Returns `{"status": "ok", "model_loaded": true}` or `503` if model failed to load.

### `POST /predict`
**Request:** `multipart/form-data` with `file` (JPEG or PNG).

**Response (200):**
```json
{
  "prediction": "pneumonia",
  "confidence": 0.8734,
  "heatmap_base64": "iVBORw0KGgo...",
  "pathology_scores": {
    "Atelectasis": 0.1234,
    "Pneumonia": 0.8734,
    "Effusion": 0.0512,
    ...
  }
}
```

**Errors:**
- `400` — invalid file type or unreadable image
- `500` — inference failure with `{"error": "<detail>"}`

## Dependencies
`torch`, `torchvision`, `torchxrayvision`, `captum`, `scikit-image`, `fastapi`, `uvicorn`, `Pillow`, `numpy`, `matplotlib`
