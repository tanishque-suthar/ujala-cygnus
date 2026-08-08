# Agent Instructions — Model Server

## Tech
FastAPI, Python. Runs on `localhost:8001`.

## Responsibility
Loads a pretrained chest X-ray classification model, runs inference on uploaded images, and returns a prediction with an explainability heatmap. Leaf service — calls nothing upstream.

## Model backends

Two backends are supported, selected at startup via the `MODEL_BACKEND` env var (default: `biomedclip`).

### Active backend: BiomedCLIP + LoRA (`MODEL_BACKEND=biomedclip`)

**Base model:** `microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224` loaded via `open_clip.create_model_and_transforms`. Only the vision tower (`clip_model.visual`, timm-wrapped ViT) is used — the text tower is discarded.

**LoRA fine-tuning:** Last 6 transformer blocks (`trunk.blocks[6..11]`) have LoRA adapters injected into the Q and V projections of the fused `qkv` Linear. K and the output projection are frozen. Config: `r=8`, `alpha=16`, `dropout=0.05`. State dict key pattern: `encoder.trunk.blocks.{idx}.attn.qkv.lora_q/lora_v.lora_A/lora_B`.

**Checkpoint:** `biomedclip/best_checkpoint.pt` (overridable via `CHECKPOINT_PATH`). Fine-tuned on NIH dataset with MAPLES-style labels. Load key: `model_state_dict`. Verified by asserting exactly 24 LoRA keys at startup.

**Thresholds:** `biomedclip/calibrated_thresholds.json` (overridable via `THRESHOLDS_PATH`). Per-class sigmoid thresholds calibrated via Youden's J statistic on the validation set. Loaded at startup.

**Labels (13, multi-label):**
`enlarged cardiomediastinum`, `cardiomegaly`, `atelectasis`, `consolidation`, `lung edema`, `fracture`, `lung lesion`, `pleural effusion`, `pneumonia`, `pneumothorax`, `support device`, `lung opacity`, `pleural other`

**Preprocessing pipeline:**
1. Convert to RGB
2. Resize to 224×224
3. Normalize with mean/std pulled from open_clip's own validation transform (fallback: `mean=(0.4815, 0.4578, 0.4082)`, `std=(0.2686, 0.2613, 0.2758)`)
4. No augmentation

**Inference flow:**
1. Forward pass → raw logits `(1, 13)`
2. `torch.sigmoid` → per-class probabilities
3. Build `pathology_scores` dict (all 13, rounded to 4 decimals)
4. Build `op_threshs` dict from `calibrated_thresholds.json`
5. Find all labels where `prob >= threshold`
6. If any → pick highest-scoring as prediction; its score = `confidence`
7. If none → `prediction = "normal"`, `confidence = 0.0`; Grad-CAM targets highest-scoring label

**Grad-CAM target:** `model.encoder.trunk.blocks[-1]` (last ViT transformer block)

---

### Fallback backend: DenseNet121 (`MODEL_BACKEND=densenet`)

TorchXRayVision's `DenseNet121` with `densenet121-res224-all` weights (overridable via `MODEL_WEIGHTS`). Multi-label classifier covering 18 pathologies across NIH, CheXpert, MIMIC-CXR, PadChest, etc.

Pathologies: Atelectasis, Consolidation, Infiltration, Pneumothorax, Edema, Emphysema, Fibrosis, Effusion, **Pneumonia**, Pleural_Thickening, Cardiomegaly, Nodule, Mass, Hernia, Lung Lesion, Fracture, Lung Opacity, Enlarged Cardiomediastinum

Weights are auto-downloaded by torchxrayvision to `~/.torchxrayvision/` on first load.

**Preprocessing pipeline:**
1. Convert to grayscale (PIL `"L"` mode)
2. Normalize pixel values from [0, 255] to [-1024, 1024] via `xrv.datasets.normalize(img, 255)`
3. Add channel dimension → shape `(1, H, W)`
4. Center crop via `xrv.datasets.XRayCenterCrop()`
5. Resize to 224×224 via `xrv.datasets.XRayResizer(224)`
6. Convert to tensor, unsqueeze batch dim → final shape `(1, 1, 224, 224)`

**Inference flow:**
The model is loaded with `apply_sigmoid=False`, and its `op_threshs` are saved to `saved_op_threshs` and then nulled (`model.op_threshs = None`). **Never read `model.op_threshs` after load — it is `None`; use `saved_op_threshs`.**

1. Forward pass → raw logits `(1, 18)`
2. `torch.sigmoid` → per-pathology probabilities
3. Build `pathology_scores` from all 18 sigmoid values (rounded to 4 decimals)
4. Build `op_threshs` from `model.saved_op_threshs`
5. Find all pathologies (excluding `"Lung Opacity"`) where `prob >= threshold`
6. If any → pick highest-scoring; its score = `confidence`
7. If none → `prediction = "normal"`, `confidence = 0.0`

**Grad-CAM target:** `model.features[-1]` (final DenseBlock)

---

## File Structure

| File | Purpose |
|---|---|
| `inference.py` | Model loading, preprocessing, Grad-CAM, prediction logic — dispatches on `MODEL_BACKEND` |
| `biomedclip_model.py` | BiomedCLIP+LoRA architecture (`LoRALinear`, `QKVLoRALinear`, `BiomedCLIPLoRA`), label list, threshold loader |
| `main.py` | FastAPI app, lifespan, endpoints, CORS |
| `app_config.py` | Pydantic settings (`model_backend`, `checkpoint_path`, `thresholds_path`, `model_weights`) |
| `requirements.txt` | Python dependencies |

Note: the inference module is named `inference.py` (not `model.py`) to avoid shadowing torchxrayvision's internal `model` package.
Note: the config module is named `app_config.py` (not `config.py`) to avoid shadowing torchxrayvision's internal `config` package.

## Env vars

| Var | Default | Effect |
|---|---|---|
| `MODEL_BACKEND` | `biomedclip` | `"biomedclip"` or `"densenet"` |
| `CHECKPOINT_PATH` | `biomedclip/best_checkpoint.pt` | BiomedCLIP checkpoint path |
| `THRESHOLDS_PATH` | `biomedclip/calibrated_thresholds.json` | Per-class threshold file path |
| `MODEL_WEIGHTS` | `densenet121-res224-all` | DenseNet weights tag (ignored when backend is biomedclip) |

## Endpoints

### `GET /health`
Returns `{"status": "ok", "model_loaded": true, "model_backend": "biomedclip"}`, or `503` with `{"status": "error", "model_loaded": false, "model_backend": "..."}` if the model failed to load.

### `POST /predict`
**Request:** `multipart/form-data` with `file` (JPEG or PNG).

**Response (200):**
```json
{
  "prediction": "consolidation",
  "confidence": 0.8721,
  "heatmap_base64": "iVBORw0KGgo...",
  "pathology_scores": {
    "atelectasis": 0.1234,
    "consolidation": 0.8721,
    "pneumonia": 0.0542,
    "lung opacity": 0.3123,
    ...
  },
  "op_threshs": {
    "atelectasis": 0.5,
    "consolidation": 0.45,
    "pneumonia": 0.3,
    "lung opacity": 0.45,
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

**Errors:**
- `400` — invalid file type, unreadable image, or image that fails to decode
- `500` — inference failure with `{"error": "<detail>"}`

Inference runs off the event loop via `asyncio.get_running_loop().run_in_executor()` so the model call does not block the async server.

## Grad-CAM notes (ViT backend)
ViT Grad-CAM attribution is more diffuse than CNN Grad-CAM because self-attention aggregates globally. Heatmaps will look less localized than DenseNet's — this is expected. The same two-step resize (224×224 → min_dim) and centered canvas placement logic is used for both backends.

## Dependencies
`torch`, `torchvision`, `open-clip-torch`, `timm`, `torchxrayvision`, `captum`, `scikit-image`, `fastapi`, `uvicorn[standard]`, `python-multipart`, `pydantic-settings`, `Pillow`, `numpy`, `matplotlib`
