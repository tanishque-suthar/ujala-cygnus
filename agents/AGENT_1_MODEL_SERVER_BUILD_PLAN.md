# Build Plan: Replace stub model server with real BiomedCLIP + LoRA inference

## Context

`classifier_model/best_biomedclip_model.pth` is a PEFT LoRA adapter (116 keys) for
`microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224`. The stub at
`stub_model_server/main.py` needs to be replaced with actual inference.

## Decisions (confirmed with user)

| Question | Answer |
|---|---|
| Classification method | Zero-shot CLIP (text prompt similarity) — no classifier head |
| Preprocessing | BiomedCLIP defaults (HuggingFace `AutoProcessor`) |
| LoRA loading | PEFT's `PeftModel.from_pretrained()` |
| Heatmap | Attention rollout on ViT attention weights |
| Weights path env var | `MODEL_WEIGHTS_PATH` (default `./classifier_model/best_biomedclip_model.pth`) |

## Files to create / modify

### 1. `stub_model_server/config.py` (new)
- `Settings` with `model_weights_path: str = "./classifier_model/best_biomedclip_model.pth"`

### 2. `stub_model_server/model.py` (new)
- **Model loading**: `AutoModel.from_pretrained("microsoft/...")` → `PeftModel.from_pretrained(..., weights_path)` → `model.eval()`
- **Text prompts**: Encode once at startup (`"a chest X-ray showing pneumonia"`, `"a normal chest X-ray"`)
- **Preprocessing**: `AutoProcessor.from_pretrained(...)` — 224×224, CLIP norm, grayscale→RGB
- **Inference**: image embedding → cosine similarity with text embeddings → softmax → prediction + confidence
- **Heatmap**: `output_attentions=True` → attention rollout → colormap overlay → base64 PNG

### 3. `stub_model_server/main.py` (replace)
- Lifespan loading, `GET /health`, `POST /predict`, error handling, CORS

### 4. `stub_model_server/requirements.txt` (new)
- `torch>=2.0.0`, `transformers>=4.35.0`, `peft>=0.7.0`, `Pillow`, `numpy`, `opencv-python-headless`, `fastapi`, `uvicorn[standard]`, `python-multipart`

## Post-deployment

Update Backend env var `ACTIVE_MODEL_NAME=biomedclip` (currently `densenet121`).
