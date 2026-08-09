import json
import math
from pathlib import Path

import open_clip
import torch
import torch.nn as nn

from app_config import settings

# Resolve relative paths against the project root (parent of stub_model_server/)
REPO_ROOT = Path(__file__).parent.parent

BIOMEDCLIP_LABELS = [
    "enlarged cardiomediastinum",
    "cardiomegaly",
    "atelectasis",
    "consolidation",
    "lung edema",
    "fracture",
    "lung lesion",
    "pleural effusion",
    "pneumonia",
    "pneumothorax",
    "support device",
    "lung opacity",
    "pleural other",
]

_model = None
_thresholds: dict[str, float] = {}
_preprocess = None


class LoRALinear(nn.Module):
    def __init__(self, in_features: int, out_features: int, r: int, alpha: float, dropout: float):
        super().__init__()
        self.r = r
        self.scale = alpha / r
        self.lora_A = nn.Parameter(torch.empty(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        self.dropout = nn.Dropout(dropout)
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)


class QKVLoRALinear(nn.Module):
    """Wraps the fused qkv Linear of a timm ViT block.

    The Q and V slices get LoRA adapters (lora_q, lora_v); the K slice stays frozen.
    State dict keys under this module:
        qkv.weight / qkv.bias      — frozen base linear
        lora_q.lora_A / lora_q.lora_B
        lora_v.lora_A / lora_v.lora_B
    """

    def __init__(self, qkv_linear: nn.Linear, r: int, alpha: float, dropout: float):
        super().__init__()
        self.qkv = qkv_linear
        in_features = qkv_linear.in_features
        # qkv_linear.out_features == 3 * head_dim * num_heads; each slice is 1/3
        slice_dim = qkv_linear.out_features // 3
        self.lora_q = LoRALinear(in_features, slice_dim, r, alpha, dropout)
        self.lora_v = LoRALinear(in_features, slice_dim, r, alpha, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        qkv = self.qkv(x)
        slice_dim = qkv.shape[-1] // 3
        q, k, v = qkv[..., :slice_dim], qkv[..., slice_dim:2 * slice_dim], qkv[..., 2 * slice_dim:]
        q = q + self.lora_q(x)
        v = v + self.lora_v(x)
        return torch.cat([q, k, v], dim=-1)


class BiomedCLIPLoRA(nn.Module):
    def __init__(self, r: int = 8, alpha: float = 16.0, dropout: float = 0.05, num_lora_blocks: int = 6):
        super().__init__()
        clip_model, _, val_transform = open_clip.create_model_and_transforms(
            "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
        )
        self._val_transform = val_transform

        if not hasattr(clip_model.visual, "trunk"):
            raise RuntimeError(
                "BiomedCLIP visual backbone does not have a 'trunk' attribute — "
                "this checkpoint requires the timm backend (vit_base_patch16_224)."
            )

        self.encoder = clip_model.visual
        for param in self.encoder.parameters():
            param.requires_grad_(False)

        blocks = self.encoder.trunk.blocks
        num_blocks = len(blocks)
        if num_blocks != 12:
            import warnings
            warnings.warn(
                f"Expected 12 ViT blocks, found {num_blocks}. "
                "Adjust num_lora_blocks or the target block range if needed."
            )
        target_indices = list(range(num_blocks - num_lora_blocks, num_blocks))

        for idx in target_indices:
            original_qkv = blocks[idx].attn.qkv
            blocks[idx].attn.qkv = QKVLoRALinear(original_qkv, r=r, alpha=alpha, dropout=dropout)

        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224)
            embed_dim = self.encoder(dummy).shape[-1]

        self.head = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Dropout(0.1),
            nn.Linear(embed_dim, len(BIOMEDCLIP_LABELS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.encoder(x)
        return self.head(features)

    @property
    def val_transform(self):
        return self._val_transform


def _extract_norm_stats(transform):
    """Pull mean/std from open_clip's returned validation transform pipeline."""
    import torchvision.transforms as T
    for t in transform.transforms:
        if isinstance(t, T.Normalize):
            return t.mean, t.std
    # Fallback to BiomedCLIP training stats if Normalize layer not found
    return (0.4815, 0.4578, 0.4082), (0.2686, 0.2613, 0.2758)


def load_biomedclip(device: torch.device) -> tuple[BiomedCLIPLoRA, dict[str, float]]:
    model = BiomedCLIPLoRA(r=8, alpha=16.0, dropout=0.05, num_lora_blocks=6)

    ckpt_path = Path(settings.checkpoint_path)
    if not ckpt_path.is_absolute():
        ckpt_path = REPO_ROOT / ckpt_path
    thresh_path = Path(settings.thresholds_path)
    if not thresh_path.is_absolute():
        thresh_path = REPO_ROOT / thresh_path

    ckpt = torch.load(ckpt_path, map_location=device)

    lora_keys = [k for k in ckpt["model_state_dict"].keys() if "lora" in k]
    expected = 24  # 6 blocks × 2 projections (q, v) × 2 params (A, B)
    assert len(lora_keys) == expected, (
        f"LoRA key count mismatch: expected {expected}, got {len(lora_keys)}.\n"
        f"Found keys: {lora_keys}"
    )

    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    model.to(device)

    thresholds: dict[str, float] = json.loads(thresh_path.read_text())

    return model, thresholds


def get_biomedclip_preprocess(model: BiomedCLIPLoRA):
    """Build the inference preprocessing transform from the model's own val transform."""
    import torchvision.transforms as T
    mean, std = _extract_norm_stats(model.val_transform)
    return T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=mean, std=std),
    ])


def init_biomedclip_model(device: torch.device):
    global _model, _thresholds, _preprocess
    _model, _thresholds = load_biomedclip(device)
    _preprocess = get_biomedclip_preprocess(_model)


def get_biomedclip_model():
    if _model is None:
        raise RuntimeError("BiomedCLIP model not initialized")
    return _model, _thresholds, _preprocess
