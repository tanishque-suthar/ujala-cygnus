# BiomedCLIP + LoRA — Integration Reference

Notes for loading and running this finetuned model in production (inference only).

## Base model
- `microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224` loaded via `open_clip.create_model_and_transforms(...)`.
- Only the **vision tower** (`clip_model.visual`) is used. Discard the text tower — this is an image-only classifier, not a CLIP similarity model.
- Auto-detect backend: `hasattr(clip_model.visual, 'trunk')` → timm-wrapped ViT (this checkpoint's actual backend); else native `open_clip` ViT. The reconstruction code must match whichever backend was used at train time — verify by checking `visual.trunk` exists before loading weights.

## Model architecture to reconstruct before loading weights
LoRA adapters are part of the model graph, not a separate merge-able artifact — you must rebuild the exact same module structure before calling `load_state_dict`, then load weights.

1. Freeze the vision tower.
2. Inject LoRA into **Q and V projections only** (K and output projection untouched) of the **last 6 transformer blocks** of the ViT.
   - timm backend: replace `blocks[idx].attn.qkv` with a wrapper that adds separate low-rank adapters to the Q and V slices of the fused qkv output (K slice unchanged).
   - native open_clip backend: replace `blocks[idx].attn` (an `nn.MultiheadAttention`) with a custom attention module that splits the fused in-projection into separate Q/K/V linears, adds LoRA to Q and V, keeps K and out_proj frozen.
3. LoRA math: `output = frozen_linear(x) + (alpha/r) * dropout(x) @ A^T @ B^T`.
4. Append classification head: `nn.Sequential(LayerNorm(embed_dim), Dropout(0.1), Linear(embed_dim, 13))` on top of the encoder output. `embed_dim` is inferred at train time from a dummy forward pass through `clip_model.encode_image` (not read from a fixed attribute) — verify it matches the checkpoint's head input size.

Use the reference implementation from the training notebook (`LoRALinear`, `LoRAAdapter`, `QKVLoRALinear`, `LoRAMultiheadAttention`, `BiomedCLIPLoRA` classes) rather than reimplementing from scratch, to guarantee the state dict keys line up.

## LoRA hyperparameters (must match training exactly)
| Param | Value |
|---|---|
| Rank `r` | 8 |
| Alpha | 16 |
| Dropout | 0.05 (irrelevant at inference — set `model.eval()`) |
| Target blocks | last 6 transformer blocks |
| Target projections | Q, V only |

## Checkpoint format
Saved via `torch.save(dict(...))`, load with `torch.load(path, map_location=device)`. Keys:
- `model_state_dict` — full model state dict (frozen backbone + LoRA adapters + head); load via `model.load_state_dict(ckpt['model_state_dict'])` onto the reconstructed architecture above.
- `epoch`, `best_auc`, `history`, `optimizer_state_dict`, `scheduler_state_dict` — training-only, not needed for inference.
- Use `best_checkpoint.pt` (selected by validation macro AUC), not an arbitrary epoch checkpoint.
- A companion `calibrated_thresholds.json` holds per-class decision thresholds (see below) — load this alongside the checkpoint.

## Input preprocessing (must match exactly)
- Resize to **224×224**.
- Normalize with the mean/std pulled from BiomedCLIP's own preprocessing transform at train time (not generic OpenAI-CLIP stats) — pull these from `open_clip.create_model_and_transforms(MODEL_NAME)`'s returned validation transform rather than hardcoding, and confirm they match the fallback `(0.4815, 0.4578, 0.4082)` / `(0.2686, 0.2613, 0.2758)` used only if a `Normalize` transform couldn't be found.
- No augmentation at inference (no random affine, no color jitter, no flip).
- Convert image to RGB before preprocessing.

## Output / labels
Model outputs 13 raw logits, one per class, in this exact order:
```
['enlarged cardiomediastinum', 'cardiomegaly', 'atelectasis', 'consolidation',
 'lung edema', 'fracture', 'lung lesion', 'pleural effusion', 'pneumonia',
 'pneumothorax', 'support device', 'lung opacity', 'pleural other']
```
This is **multi-label**, not multi-class — apply `sigmoid` independently per class (no softmax).

For binary predictions, threshold each class's sigmoid probability using the **per-class calibrated thresholds** in `calibrated_thresholds.json` (not a flat 0.5) — these were tuned per class on the validation set via Youden's J statistic and materially differ from 0.5 for imbalanced classes. If a probability score (not just yes/no) is all the app needs, thresholds aren't required — just report the sigmoid outputs.

## Inference mode requirements
- `model.eval()` before inference (disables LoRA dropout).
- Run under `torch.no_grad()`.
- If deployed on a single GPU/CPU, drop the `nn.DataParallel` wrapper used in training — that was only for 2×T4 training-time parallelism.
