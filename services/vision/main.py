"""Optional internal-only visual QA service for manuscript images.
Does not perform OCR, medical diagnosis, or automatically publish classical text.
"""
import io
import os
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
import cv2
import numpy as np

app = FastAPI(title="AyurSutra manuscript-image inspector", docs_url=None, redoc_url=None)

@app.get("/health")
def health():
    return {"ok": True, "service": "manuscript-image-inspector", "capabilities": ["image-dimensions", "blur-score"], "ocr": False}

@app.post("/v1/inspect")
async def inspect(file: UploadFile = File(...), x_internal_key: str | None = Header(default=None)):
    from hmac import compare_digest
    token = os.getenv("AYURSUTRA_VISION_KEY", "")
    if len(token) < 32 or not x_internal_key or not compare_digest(token, x_internal_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(status_code=415, detail="PNG or JPEG required")
    data = await file.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds 8MB")
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data)).convert('L')
        if img.width * img.height > 24_000_000:
            raise ValueError("Image too large")
    except (UnidentifiedImageError, ValueError, OSError):
        raise HTTPException(status_code=422, detail="Invalid image")
    frame = np.asarray(img)
    focus_variance = float(cv2.Laplacian(frame, cv2.CV_64F).var())
    return {"width":img.width, "height":img.height, "focus_variance":round(focus_variance,2),
            "notice":"Heuristic focus measurement only; requires review. No text recognition performed."}
