import base64
import io

import numpy as np
import torch
import torchvision
import torchxrayvision as xrv
from captum.attr import LayerGradCam
from PIL import Image

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model = None

def load_model():
    model = xrv.models.DenseNet(weights="densenet121-res224-all")
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
    img = img[None, :, :]
    transform = torchvision.transforms.Compose([
        xrv.datasets.XRayCenterCrop(),
        xrv.datasets.XRayResizer(224),
    ])
    img = transform(img)
    return torch.from_numpy(img).unsqueeze(0).to(DEVICE)

def _generate_gradcam(model, pixel_values, target_idx, original_image):
    input_tensor = pixel_values.clone().requires_grad_(True)
    layer_gc = LayerGradCam(model, model.features[-1])

    attribution = layer_gc.attribute(input_tensor, target=target_idx)
    cam = torch.relu(attribution).squeeze().cpu().detach().numpy()
    cam = cam / (cam.max() + 1e-8)

    cam_pil = Image.fromarray(cam.astype(np.float32))
    cam_pil = cam_pil.resize(original_image.size, Image.Resampling.BICUBIC)
    cam_resized = np.array(cam_pil, dtype=np.float32)

    from matplotlib import colormaps
    heatmap_rgba = colormaps["inferno"](cam_resized)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)

    original_np = np.array(original_image.convert("RGB"), dtype=np.float32)
    alpha = cam_resized[:, :, np.newaxis] * 0.75
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

    pneumonia_idx = model.pathologies.index("Pneumonia")
    pneumonia_prob = float(probs[pneumonia_idx])
    threshold = float(model.op_threshs[pneumonia_idx])

    prediction = "pneumonia" if pneumonia_prob >= threshold else "normal"
    confidence = pneumonia_prob if prediction == "pneumonia" else (1.0 - pneumonia_prob)

    heatmap_base64 = _generate_gradcam(model, pixel_values, pneumonia_idx, image)

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "heatmap_base64": heatmap_base64,
        "pathology_scores": pathology_scores,
    }