# Cygnus — Chest X-Ray Screening System

A three-service medical screening application that classifies chest X-ray images using a DenseNet121 model (TorchXRayVision) and explains predictions via Grad-CAM heatmaps.

## Architecture

| Service | Port | Tech | Depends on |
|---------|------|------|------------|
| Model Server | `localhost:8001` | FastAPI / Python | nothing (leaf) |
| Backend | `localhost:8000` | FastAPI / Python | Model Server |
| Frontend | `localhost:3000` | React / Vite / Tailwind CSS | Backend |

Request flow is strictly one-directional: **Frontend -> Backend -> Model Server**. The Frontend never calls the Model Server directly; the Model Server never calls anything upstream.

## Repo structure

```
cygnus-densenet-migration/
  agents/              Agent instruction files for each service
  backend/             FastAPI application layer, SQLite persistence
  frontend/            React portal (dashboard, upload, patient history)
  stub_model_server/   Standalone inference server (DenseNet121 + Grad-CAM)
  database/            SQLite DB and file uploads
```

## Services

- **Model Server** (`stub_model_server/`) — DenseNet121 inference + Grad-CAM heatmaps, exposed via `GET /health` and `POST /predict`.
- **Backend** (`backend/`) — Application layer that uploads images, delegates to Model Server, and persists results in SQLite.
- **Frontend** (`frontend/`) — React portal with X-ray screening, patient records, and a dashboard.

Detailed instructions for each service are in `agents/` (`AGENT_1_MODEL_SERVER.md`, `AGENT_2_BACKEND.md`, `AGENT_3_FRONTEND.md`).
