import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from model import init_model, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_model()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    from model import get_model

    try:
        get_model()
        return {"status": "ok", "model_loaded": True}
    except RuntimeError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "model_loaded": False},
        )


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png"}
    if file.content_type not in allowed:
        return JSONResponse(
            status_code=400,
            content={"error": "File must be JPEG or PNG"},
        )

    try:
        contents = await file.read()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Failed to read uploaded file"},
        )

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Uploaded file is not a valid image"},
        )

    try:
        result = predict(image)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
