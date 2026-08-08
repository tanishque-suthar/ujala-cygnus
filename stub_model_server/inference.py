import base64
import importlib
import io
import sys

# Captum may not be installed in this venv (disk full). Fall back to the sibling project venv.
_SIBLING_SITE = "/home/tsvd/Desktop/projects/cygnus/venv/lib/python3.12/site-packages"
try:
    importlib.import_module("captum")
except ModuleNotFoundError:
    if _SIBLING_SITE not in sys.path:
        sys.path.insert(0, _SIBLING_SITE)

import numpy as np
import torch
from matplotlib import colormaps
from PIL import Image

from app_config import settings

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── DenseNet state ────────────────────────────────────────────────────────────

_densenet_model = None
_densenet_transform = None


def _get_densenet_transform():
    global _densenet_transform
    if _densenet_transform is None:
        import torchvision
        import torchxrayvision as xrv
        _densenet_transform = torchvision.transforms.Compose([
            xrv.datasets.XRayCenterCrop(),
            xrv.datasets.XRayResizer(224),
        ])
    return _densenet_transform


def _load_densenet():
    import torchxrayvision as xrv
    # Save original op_threshs before nulling them: the model checks
    # op_threshs internally and applies a second sigmoid if not None.
    # We handle sigmoid + threshold comparison manually in predict().
    model = xrv.models.DenseNet(weights=settings.model_weights, apply_sigmoid=False)
    model.saved_op_threshs = model.op_threshs
    model.op_threshs = None
    model.eval()
    model.to(DEVICE)
    return model


def _init_densenet():
    global _densenet_model
    _densenet_model = _load_densenet()


def _get_densenet():
    if _densenet_model is None:
        raise RuntimeError("DenseNet model not initialized")
    return _densenet_model


# ── BiomedCLIP state ──────────────────────────────────────────────────────────

def _init_biomedclip():
    from biomedclip_model import init_biomedclip_model
    init_biomedclip_model(DEVICE)


def _get_biomedclip():
    from biomedclip_model import get_biomedclip_model
    return get_biomedclip_model()


# ── Shared init / get ─────────────────────────────────────────────────────────

def init_model():
    if settings.model_backend == "biomedclip":
        _init_biomedclip()
    elif settings.model_backend == "densenet":
        _init_densenet()
    else:
        raise ValueError(f"Unknown MODEL_BACKEND: '{settings.model_backend}' — must be 'biomedclip' or 'densenet'")


def get_model():
    if settings.model_backend == "biomedclip":
        return _get_biomedclip()[0]
    return _get_densenet()


# ── Preprocessing ─────────────────────────────────────────────────────────────

def _preprocess_densenet(image: Image.Image) -> torch.Tensor:
    import torchxrayvision as xrv
    img = np.array(image.convert("L"), dtype=np.float32)
    img = xrv.datasets.normalize(img, 255)
    img = img[np.newaxis, ...]
    img = _get_densenet_transform()(img)
    return torch.from_numpy(img).unsqueeze(0).to(DEVICE)


def _preprocess_biomedclip(image: Image.Image) -> torch.Tensor:
    _, _, preprocess = _get_biomedclip()
    return preprocess(image.convert("RGB")).unsqueeze(0).to(DEVICE)


# ── Grad-CAM ──────────────────────────────────────────────────────────────────

def _generate_gradcam(model, pixel_values: torch.Tensor, target_idx: int, original_image, backend: str) -> str:
    from captum.attr import LayerGradCam
    input_tensor = pixel_values.clone().requires_grad_(True)

    if backend == "biomedclip":
        target_layer = model.encoder.trunk.blocks[-1]
    else:
        target_layer = model.features[-1]

    layer_gc = LayerGradCam(model, target_layer)
    attribution = layer_gc.attribute(input_tensor, target=target_idx)
    cam = torch.relu(attribution).squeeze().cpu().detach().numpy()
    cam = cam / (cam.max() + 1e-8)

    w, h = original_image.size
    min_dim = min(h, w)

    # Resize through 224×224 first to match the model's actual feature space,
    # then up to the cropped square size for overlay alignment
    cam_pil = Image.fromarray(cam.astype(np.float32))
    cam_pil = cam_pil.resize((224, 224), Image.Resampling.BICUBIC)
    cam_pil = cam_pil.resize((min_dim, min_dim), Image.Resampling.BICUBIC)
    cam_resized_square = np.array(cam_pil, dtype=np.float32)

    cam_full = np.zeros((h, w), dtype=np.float32)
    start_y = (h - min_dim) // 2
    start_x = (w - min_dim) // 2
    cam_full[start_y:start_y + min_dim, start_x:start_x + min_dim] = cam_resized_square

    heatmap_rgba = colormaps["inferno"](cam_full)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)

    original_np = np.array(original_image.convert("RGB"), dtype=np.float32)
    alpha = cam_full[:, :, np.newaxis] * 0.75
    overlay = np.clip(
        original_np * (1.0 - alpha) + heatmap_rgb.astype(np.float32) * alpha,
        0, 255,
    ).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ── Prediction ────────────────────────────────────────────────────────────────

def _predict_densenet(image: Image.Image) -> dict:
    model = _get_densenet()
    pixel_values = _preprocess_densenet(image)

    with torch.no_grad():
        logits = model(pixel_values)

    probs = torch.sigmoid(logits[0]).cpu().numpy()
    pathology_scores = {
        name: round(float(probs[i]), 4)
        for i, name in enumerate(model.pathologies)
    }
    op_threshs = {
        name: float(model.saved_op_threshs[i])
        for i, name in enumerate(model.pathologies)
    }

    candidates = [
        (i, name, float(probs[i]))
        for i, name in enumerate(model.pathologies)
        if name != "Lung Opacity" and float(probs[i]) >= float(model.saved_op_threshs[i])
    ]

    if candidates:
        target_idx, prediction, confidence = max(candidates, key=lambda x: x[2])
    else:
        prediction = "normal"
        confidence = 0.0
        overall_max = max(
            ((i, float(probs[i])) for i in range(len(model.pathologies))),
            key=lambda x: x[1],
        )
        target_idx = overall_max[0]

    heatmap_base64 = _generate_gradcam(model, pixel_values, target_idx, image, "densenet")

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "heatmap_base64": heatmap_base64,
        "pathology_scores": pathology_scores,
        "op_threshs": op_threshs,
    }


def _predict_biomedclip(image: Image.Image) -> dict:
    from biomedclip_model import BIOMEDCLIP_LABELS
    model, thresholds, _ = _get_biomedclip()
    pixel_values = _preprocess_biomedclip(image)

    with torch.no_grad():
        logits = model(pixel_values)

    probs = torch.sigmoid(logits[0]).cpu().numpy()
    pathology_scores = {
        label: round(float(probs[i]), 4)
        for i, label in enumerate(BIOMEDCLIP_LABELS)
    }
    op_threshs = {label: thresholds[label] for label in BIOMEDCLIP_LABELS}

    candidates = [
        (i, label, float(probs[i]))
        for i, label in enumerate(BIOMEDCLIP_LABELS)
        if float(probs[i]) >= thresholds[label]
    ]

    if candidates:
        target_idx, prediction, confidence = max(candidates, key=lambda x: x[2])
    else:
        prediction = "normal"
        confidence = 0.0
        target_idx = int(np.argmax(probs))

    heatmap_base64 = _generate_gradcam(model, pixel_values, target_idx, image, "biomedclip")

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "heatmap_base64": heatmap_base64,
        "pathology_scores": pathology_scores,
        "op_threshs": op_threshs,
    }


def predict(image: Image.Image) -> dict:
    if settings.model_backend == "biomedclip":
        return _predict_biomedclip(image)
    return _predict_densenet(image)