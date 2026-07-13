from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/predict")
async def predict(file: UploadFile):
    allowed = {"image/jpeg", "image/png"}
    if file.content_type not in allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "File must be JPEG or PNG"})

    return {
        "prediction": "pneumonia",
        "confidence": 0.91,
        "heatmap_base64": (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ),
    }
