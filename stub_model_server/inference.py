import base64
import io

import numpy as np
import torch
import torchvision
import torchxrayvision as xrv
from captum.attr import LayerGradCam
from matplotlib import colormaps
from PIL import Image

from config import settings

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model = None

_transform = torchvision.transforms.Compose([
    xrv.datasets.XRayCenterCrop(),
    xrv.datasets.XRayResizer(224),
])

def load_model():
    # Save original op_threshs before nulling them: the model checks
    # op_threshs internally and applies a second sigmoid if not None.
    # We handle sigmoid + threshold comparison manually in predict().
    model = xrv.models.DenseNet(weights=settings.model_weights, apply_sigmoid=False)
    model.saved_op_threshs = model.op_threshs
    model.op_threshs = None
    model.eval()
    model.to(DEVICE)
    return model

def init_model():
    global _model
    _model = load_model()

def get_model():
    if _model is None:
        raise RuntimeError("Model not initialized")
    return _model

def preprocess_image(image: Image.Image):
    img = np.array(image.convert("L"), dtype=np.float32)
    img = xrv.datasets.normalize(img, 255)
    
    # Add channel dimension -> shape (1, H, W)
    img = img[np.newaxis, ...]
    
    img = _transform(img)
    
    # Convert to tensor, unsqueeze batch dim -> final shape (1, 1, 224, 224)
    pixel_values = torch.from_numpy(img).unsqueeze(0).to(DEVICE)
    return pixel_values

def _generate_gradcam(model, pixel_values, target_idx, original_image):
    input_tensor = pixel_values.clone().requires_grad_(True)
    layer_gc = LayerGradCam(model, model.features[-1])

    attribution = layer_gc.attribute(input_tensor, target=target_idx)
    cam = torch.relu(attribution).squeeze().cpu().detach().numpy()
    cam = cam / (cam.max() + 1e-8)

    w, h = original_image.size
    min_dim = min(h, w)
    
    # Resize through 224x224 first to match the model's actual feature space,
    # then up to the cropped square size for overlay alignment
    cam_pil = Image.fromarray(cam.astype(np.float32))
    cam_pil = cam_pil.resize((224, 224), Image.Resampling.BICUBIC)
    cam_pil = cam_pil.resize((min_dim, min_dim), Image.Resampling.BICUBIC)
    cam_resized_square = np.array(cam_pil, dtype=np.float32)
    
    # Create a full-size cam array filled with zeros (no heat)
    cam_full = np.zeros((h, w), dtype=np.float32)
    start_y = (h - min_dim) // 2
    start_x = (w - min_dim) // 2
    
    # Place the square heatmap into the correct center position
    cam_full[start_y:start_y + min_dim, start_x:start_x + min_dim] = cam_resized_square

    heatmap_rgba = colormaps["inferno"](cam_full)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)

    original_np = np.array(original_image.convert("RGB"), dtype=np.float32)
    alpha = cam_full[:, :, np.newaxis] * 0.75
    overlay = np.clip(
        original_np * (1.0 - alpha) + heatmap_rgb.astype(np.float32) * alpha,
        0, 255
    ).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(overlay).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def predict(image: Image.Image) -> dict:
    model = get_model()
    pixel_values = preprocess_image(image)

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

    heatmap_base64 = _generate_gradcam(model, pixel_values, target_idx, image)

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "heatmap_base64": heatmap_base64,
        "pathology_scores": pathology_scores,
        "op_threshs": op_threshs,
    }