import base64
import io

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


# ── XAI heatmap ───────────────────────────────────────────────────────────────

def _gradient_attention_rollout(model, pixel_values: torch.Tensor, target_idx: int) -> np.ndarray:
    """Class-specific attention rollout for ViT (Chefer et al., CVPR 2021).

    Captures attention weights and their gradients w.r.t. target_idx across
    all transformer blocks, fuses them with gradient weighting, and rolls up
    through all layers to produce a (14, 14) spatial attribution map.
    """
    attentions: list[torch.Tensor] = []
    gradients: list[torch.Tensor] = []
    hooks = []

    def _fwd_hook(module, inp, out):
        attentions.append(inp[0].detach())

    def _bwd_hook(module, grad_in, grad_out):
        gradients.append(grad_in[0].detach())

    for block in model.encoder.trunk.blocks:
        hooks.append(block.attn.attn_drop.register_forward_hook(_fwd_hook))
        hooks.append(block.attn.attn_drop.register_full_backward_hook(_bwd_hook))

    input_tensor = pixel_values.clone().requires_grad_(True)

    # timm's Attention.forward skips attn_drop entirely when fused_attn is
    # True (uses F.scaled_dot_product_attention instead). Temporarily disable
    # it so the explicit code path fires and our hooks on attn_drop work.
    saved_fused = []
    for block in model.encoder.trunk.blocks:
        saved_fused.append(block.attn.fused_attn)
        block.attn.fused_attn = False

    try:
        logits = model(input_tensor)
        target_score = logits[0, target_idx]
        model.zero_grad()
        target_score.backward(retain_graph=False)
    finally:
        for block, flag in zip(model.encoder.trunk.blocks, saved_fused):
            block.attn.fused_attn = flag
        for h in hooks:
            h.remove()

    # Backward hooks fire in reverse layer order
    gradients.reverse()

    num_tokens = attentions[0].size(-1)
    rollout = torch.eye(num_tokens, device=attentions[0].device)

    for attn, grad in zip(attentions, gradients):
        attn = attn[0]  # (num_heads, N, N)
        grad = grad[0]
        weighted = torch.clamp(attn * grad, min=0)
        fused = weighted.mean(dim=0)
        fused = fused + torch.eye(num_tokens, device=fused.device)
        fused = fused / fused.sum(dim=-1, keepdim=True)
        rollout = fused @ rollout

    mask = rollout[0, 1:]  # CLS → patches, exclude CLS→CLS
    mask = mask.reshape(14, 14).cpu().numpy().astype(np.float32)
    mask_min, mask_max = mask.min(), mask.max()
    return (mask - mask_min) / (mask_max - mask_min + 1e-8)


def _densenet_gradcam(model, pixel_values: torch.Tensor, target_idx: int) -> np.ndarray:
    """Standard Grad-CAM for DenseNet (CNN). Targets the final DenseBlock."""
    from captum.attr import LayerGradCam
    input_tensor = pixel_values.clone().requires_grad_(True)
    layer_gc = LayerGradCam(model, model.features[-1])
    attribution = layer_gc.attribute(input_tensor, target=target_idx)
    cam = torch.relu(attribution).squeeze().cpu().detach().numpy()
    cam = cam.mean(axis=0) if cam.ndim == 3 else cam
    cam_max = float(cam.max())
    return cam / cam_max if cam_max > 1e-12 else np.zeros_like(cam)


def _generate_xai_heatmap(model, pixel_values: torch.Tensor, target_idx: int, original_image, backend: str) -> str:
    if backend == "biomedclip":
        cam = _gradient_attention_rollout(model, pixel_values, target_idx)
    else:
        cam = _densenet_gradcam(model, pixel_values, target_idx)

    w, h = original_image.size
    cam_pil = Image.fromarray(cam.astype(np.float32))

    if backend == "biomedclip":
        cam_pil = cam_pil.resize((w, h), Image.Resampling.BICUBIC)
        cam_full = np.array(cam_pil, dtype=np.float32)
    else:
        min_dim = min(h, w)
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

    heatmap_base64 = _generate_xai_heatmap(model, pixel_values, target_idx, image, "densenet")

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
        if label not in ["lung opacity", "support device"] and float(probs[i]) >= thresholds[label]
    ]

    if candidates:
        target_idx, prediction, confidence = max(candidates, key=lambda x: x[2])
    else:
        prediction = "normal"
        confidence = 0.0
        target_idx = int(np.argmax(probs))

    heatmap_base64 = _generate_xai_heatmap(model, pixel_values, target_idx, image, "biomedclip")

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