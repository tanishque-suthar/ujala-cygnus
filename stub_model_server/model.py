import base64
import io
import logging
import math

import numpy as np
import torch
import torch.nn.functional as F
from open_clip import create_model_from_pretrained, get_tokenizer
from peft import LoraConfig, get_peft_model
from PIL import Image

from config import settings

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"

CLASS_PROMPTS = [
    "a chest x-ray showing normal lungs",
    "a chest x-ray showing pneumonia",
]
CLASS_NAMES = ["normal", "pneumonia"]

_model = None
_preprocess = None
_tokenizer = None
_text_embeddings = None


def _build_lora_configs(model):
    n_vision_layers = len(model.visual.trunk.blocks)
    vision_targets = (
        [f"blocks.{i}.attn.qkv" for i in range(n_vision_layers)]
        + [f"blocks.{i}.attn.proj" for i in range(n_vision_layers)]
        + [f"blocks.{i}.mlp.fc1" for i in range(n_vision_layers)]
        + [f"blocks.{i}.mlp.fc2" for i in range(n_vision_layers)]
    )
    vision_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=vision_targets,
        lora_dropout=0.05,
        bias="none",
    )

    n_text_layers = len(model.text.transformer.encoder.layer)
    top_k = 4
    text_targets = (
        [f"encoder.layer.{i}.attention.self.query" for i in range(n_text_layers - top_k, n_text_layers)]
        + [f"encoder.layer.{i}.attention.self.value" for i in range(n_text_layers - top_k, n_text_layers)]
    )
    text_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=text_targets,
        lora_dropout=0.05,
        bias="none",
    )
    return vision_config, text_config


def load_model_and_processor():
    model, preprocess = create_model_from_pretrained(MODEL_NAME)
    tokenizer = get_tokenizer(MODEL_NAME)
    model.to(DEVICE)

    vision_config, text_config = _build_lora_configs(model)
    model.visual.trunk = get_peft_model(model.visual.trunk, vision_config)
    model.text.transformer = get_peft_model(model.text.transformer, text_config)

    # These were fully unfrozen (not LoRA'd) during training and are present
    # in the checkpoint as plain (non-adapter) weights.
    for p in model.visual.head.parameters():
        p.requires_grad = False  # inference only, but keep names matching state_dict
    for p in model.text.proj.parameters():
        p.requires_grad = False

    model.to(DEVICE)

    state_dict = torch.load(
        settings.model_weights_path, map_location=DEVICE, weights_only=True
    )
    result = model.load_state_dict(state_dict, strict=False)
    if result.missing_keys:
        logging.warning("Missing keys in state_dict: %s", result.missing_keys)
    if result.unexpected_keys:
        logging.warning("Unexpected keys in state_dict: %s", result.unexpected_keys)

    model.eval()
    return model, preprocess, tokenizer


@torch.no_grad()
def _encode_text_prompts(model, tokenizer):
    text_tokens = tokenizer(CLASS_PROMPTS, context_length=256).to(DEVICE)
    text_embeds = model.encode_text(text_tokens)
    text_embeds = F.normalize(text_embeds, dim=-1)
    return text_embeds


def init_model():
    global _model, _preprocess, _tokenizer, _text_embeddings
    _model, _preprocess, _tokenizer = load_model_and_processor()
    _text_embeddings = _encode_text_prompts(_model, _tokenizer)


def get_model():
    if _model is None:
        raise RuntimeError("Model not loaded — call init_model() first")
    return _model


def get_preprocess():
    if _preprocess is None:
        raise RuntimeError("Preprocess transform not loaded — call init_model() first")
    return _preprocess


def get_text_embeddings():
    if _text_embeddings is None:
        raise RuntimeError("Text embeddings not computed")
    return _text_embeddings


def preprocess_image(image: Image.Image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    preprocess = get_preprocess()
    pixel_values = preprocess(image).unsqueeze(0)
    return pixel_values.to(DEVICE)


def _register_attention_hooks(vit_trunk):
    """
    timm's VisionTransformer.forward() does not accept output_attentions
    and its Attention module does not return attention weights by default.
    We register forward hooks on each block's attn_drop (input = softmax
    attention probabilities, before dropout) to capture them manually.
    """
    captured = []

    def hook(module, input, output):
        # input[0] is the attention probability tensor fed into dropout,
        # shape: (batch, heads, tokens, tokens)
        captured.append(input[0].detach())

    handles = []
    # If the trunk is wrapped in a PeftModel, the actual blocks are at
    # vit_trunk.base_model.model.blocks
    base = vit_trunk.base_model.model if hasattr(vit_trunk, "base_model") else vit_trunk
    for blk in base.blocks:
        # Ensure fused attention kernels are disabled so attn_drop actually
        # receives materialized attention probabilities to hook into.
        if hasattr(blk.attn, "fused_attn"):
            blk.attn.fused_attn = False
        handles.append(blk.attn.attn_drop.register_forward_hook(hook))

    return captured, handles


def _compute_attention_rollout(attentions, last_n_layers: int = 4, discard_ratio: float = 0.9):
    attentions = attentions[-last_n_layers:]
    num_tokens = attentions[0].shape[-1]
    rollout = torch.eye(num_tokens, device=DEVICE)

    for attn in attentions:
        attn_mean = attn[0].mean(dim=0)  # (tokens, tokens)
        flat = attn_mean.flatten()
        threshold = flat.kthvalue(int(discard_ratio * flat.numel()))[0]
        attn_mean = torch.where(attn_mean >= threshold, attn_mean, torch.zeros_like(attn_mean))
        attn_residual = 0.5 * (attn_mean + torch.eye(num_tokens, device=DEVICE))
        attn_residual = attn_residual / attn_residual.sum(dim=-1, keepdim=True)
        rollout = attn_residual @ rollout

    cls_attention = rollout[0, 1:].cpu().numpy()
    return cls_attention


def _generate_heatmap_rgb(rollout: np.ndarray, original_size):
    from matplotlib import colormaps

    grid_size = int(math.sqrt(rollout.shape[0]))
    heatmap = rollout.reshape(grid_size, grid_size).astype(np.float32)

    lo = float(np.percentile(heatmap, 5))
    hi = float(np.percentile(heatmap, 95))
    heatmap = np.clip((heatmap - lo) / (hi - lo + 1e-8), 0.0, 1.0)

    heatmap_pil = Image.fromarray(heatmap)
    heatmap_pil = heatmap_pil.resize(original_size, Image.Resampling.BICUBIC)
    heatmap_resized = np.array(heatmap_pil, dtype=np.float32)

    cmap = colormaps["inferno"]
    heatmap_rgba = cmap(heatmap_resized)          # (H, W, 4), float32 0-1
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)
    return heatmap_rgb, heatmap_resized           # also return normalised map for alpha


@torch.no_grad()
def predict(image: Image.Image) -> dict:
    model = get_model()
    pixel_values = preprocess_image(image)
    text_embeds = get_text_embeddings()

    captured, handles = _register_attention_hooks(model.visual.trunk)
    try:
        image_embed = model.encode_image(pixel_values)
    finally:
        for h in handles:
            h.remove()

    image_embed = F.normalize(image_embed, dim=-1)

    rollout = _compute_attention_rollout(captured)
    heatmap_rgb, heat_alpha = _generate_heatmap_rgb(rollout, image.size)

    original_np = np.array(image.convert("RGB"), dtype=np.float32)
    alpha = heat_alpha[:, :, np.newaxis] * 0.75   # max 75% heatmap, scales with intensity
    overlay = np.clip(original_np * (1.0 - alpha) + heatmap_rgb.astype(np.float32) * alpha, 0, 255).astype(np.uint8)

    overlay_pil = Image.fromarray(overlay)
    buf = io.BytesIO()
    overlay_pil.save(buf, format="PNG")
    heatmap_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    logit_scale = model.logit_scale.exp()
    logits = logit_scale * (image_embed @ text_embeds.T)
    probs = logits.softmax(dim=-1).cpu().numpy()[0]

    pred_idx = int(probs.argmax())
    return {
        "prediction": CLASS_NAMES[pred_idx],
        "confidence": float(probs[pred_idx]),
        "heatmap_base64": heatmap_base64,
    }