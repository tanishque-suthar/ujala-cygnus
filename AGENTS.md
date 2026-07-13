# AGENTS.md

Chest X-ray screening system. Three services, each with a dedicated agent instruction file in `agents/`. Read the relevant file before working in that service's area.

## Architecture

| Service | Port | Tech | Talks to |
| --- | --- | --- | --- |
| Model Server | `localhost:8001` | FastAPI / Python | nothing (leaf) |
| Backend | `localhost:8000` | FastAPI / Python | Model Server only |
| Frontend | `localhost:3000` | React | Backend only |

Request flow: **Frontend → Backend → Model Server**. The Frontend must never call the Model Server directly; the Model Server must never call anything upstream.

## Per-service details

- `agents/AGENT_1_MODEL_SERVER.md` — pure inference microservice. Image in → `{prediction, confidence, heatmap_base64}` out. No auth, no business logic, no priority. Loads `.pth` weights once at startup into a module-level/global. CORS allows only `localhost:8000`.
- `agents/AGENT_2_BACKEND.md` — application layer. Validation + priority mapping + response formatting. Owns the `/screen` and `/health` endpoints. CORS allows only `localhost:3000`.
- `agents/AGENT_3_FRONTEND.md` — upload + results UI. Display only; never computes priority/confidence beyond formatting. Single page, no router needed.

When implementing, honor each file's **Explicit rules** ("Do not…") — these are hard boundaries, not suggestions.

## Key conventions & gotchas

- **Priority mapping** (Backend-only) lives in `agents/AGENT_2_BACKEND.md:29`: `>=0.85`→high, `0.6–0.85`→moderate, `<0.6`→low, but only when `prediction == "pneumonia"`; `normal` is always `low`.
- **Env vars**: `MODEL_SERVER_URL` (Backend, default `http://localhost:8001`), `ACTIVE_MODEL_NAME` (Backend, e.g. `densenet121`), and a config/env path for model weights — never hardcode the weights path.
- **Preprocessing** in Model Server must match training (resize/normalize/grayscale-RGB). Values are TBD — mark with `# CONFIRM: match training preprocessing` until provided; do not invent them.
- **Model architecture** (DenseNet121 / ViT / BiomedCLIP) is not yet finalized — keep it swappable and matching the saved `state_dict`.
- Heatmaps: Grad-CAM (CNN) or attention rollout (ViT/BiomedCLIP); returned as base64 PNG with **no** data-URI prefix.
- Error contracts: Model Server `500` → `{"error": ...}`; Backend `502` `{"error": "Model server unavailable"}` on Model Server failure/timeout (30s); Backend `413`/`400` on bad/oversized upload (>10 MB).

## OpenCode config

`opencode.json` enables the `stitch` (remote MCP) and `playwright` (local MCP) servers. Agent specs and `instructions` live in `agents/`, not inline here.

## Development practices

- **Separate git worktrees** Always make breaking changes in a new fresh git worktree.
- **Do not write excessive comments**
