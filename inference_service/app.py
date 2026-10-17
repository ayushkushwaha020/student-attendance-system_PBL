import base64
import os
import threading
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Student Attendance Face Recognition API", version="1.0.0")
API_KEY = os.environ.get("FACE_INFERENCE_API_KEY", "")
INSIGHTFACE_MODEL = os.environ.get("INSIGHTFACE_MODEL", "buffalo_l")
FACENET_THRESHOLD = float(os.environ.get("FACENET_THRESHOLD", "0.72"))
INSIGHTFACE_THRESHOLD = float(os.environ.get("INSIGHTFACE_THRESHOLD", "0.42"))
_models_lock = threading.Lock()
_models: dict[str, Any] = {}


class ImageRequest(BaseModel):
    image: str = Field(min_length=32, description="Base64 data URL or raw base64 JPEG/PNG")


class GalleryItem(BaseModel):
    student_id: int
    name: str = ""
    insightface: list[float]
    facenet: list[float]


class RecognitionRequest(ImageRequest):
    gallery: list[GalleryItem] = Field(default_factory=list, max_length=1000)


def require_key(x_api_key: str | None):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Inference API key is not configured.")
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")


def decode_image(value: str) -> np.ndarray:
    raw = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    try:
        payload = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image.") from exc
    if not payload or len(payload) > 4_000_000:
        raise HTTPException(status_code=413, detail="Image is empty or exceeds 4 MB.")
    arr = np.frombuffer(payload, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise HTTPException(status_code=400, detail="Image could not be decoded.")
    h, w = image.shape[:2]
    if w < 80 or h < 80:
        raise HTTPException(status_code=400, detail="Image is too small for recognition.")
    return image


def get_models():
    if _models:
        return _models
    with _models_lock:
        if _models:
            return _models
        from insightface.app import FaceAnalysis
        from facenet_pytorch import MTCNN, InceptionResnetV1
        import torch

        insight = FaceAnalysis(name=INSIGHTFACE_MODEL, providers=["CPUExecutionProvider"])
        insight.prepare(ctx_id=-1, det_size=(640, 640))
        device = torch.device("cpu")
        mtcnn = MTCNN(image_size=160, margin=20, keep_all=True, device=device, post_process=True)
        facenet = InceptionResnetV1(pretrained="vggface2").eval().to(device)
        _models.update({"insight": insight, "mtcnn": mtcnn, "facenet": facenet, "torch": torch})
        return _models


def normalize(vec: np.ndarray) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(v))
    if norm < 1e-9:
        raise ValueError("Empty face embedding")
    return v / norm


def extract_embeddings(image: np.ndarray) -> list[dict[str, Any]]:
    models = get_models()
    insight_faces = models["insight"].get(image)
    if not insight_faces:
        return []
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    found: list[dict[str, Any]] = []
    for face in insight_faces:
        x1, y1, x2, y2 = [int(round(float(v))) for v in face.bbox]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 - x1 < 40 or y2 - y1 < 40:
            continue
        crop = rgb[y1:y2, x1:x2]
        from PIL import Image
        faces = models["mtcnn"](Image.fromarray(crop))
        if faces is None:
            continue
        if faces.ndim == 3:
            faces = faces.unsqueeze(0)
        with models["torch"].no_grad():
            embeddings = models["facenet"](faces.to(next(models["facenet"].parameters()).device)).cpu().numpy()
        if len(embeddings) == 0:
            continue
        found.append({
            "bbox": [x1, y1, x2 - x1, y2 - y1],
            "detector_score": float(getattr(face, "det_score", 0.0)),
            "insightface": normalize(face.normed_embedding).tolist(),
            "facenet": normalize(embeddings[0]).tolist(),
        })
    return found


@app.get("/health")
def health():
    return {"ok": True, "service": "face-inference", "models_loaded": bool(_models)}


@app.post("/embed")
def embed(body: ImageRequest, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    image = decode_image(body.image)
    faces = extract_embeddings(image)
    if not faces:
        return {"ok": False, "message": "No usable face detected.", "faces": []}
    return {"ok": True, "faces": faces}


@app.post("/recognize")
def recognize(body: RecognitionRequest, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if not body.gallery:
        return {"ok": True, "result": "UNKNOWN", "message": "No enrolled embeddings are available.", "matches": []}
    image = decode_image(body.image)
    faces = extract_embeddings(image)
    if not faces:
        return {"ok": True, "result": "UNKNOWN", "message": "No face detected.", "matches": []}
    if len(faces) != 1:
        return {"ok": True, "result": "UNKNOWN", "message": "Frame must contain exactly one face for attendance matching.", "faces_detected": len(faces), "matches": []}
    probe = faces[0]
    gallery = body.gallery

    def nearest(key: str):
        p = normalize(np.asarray(probe[key], dtype=np.float32))
        scored = []
        for item in gallery:
            try:
                q = normalize(np.asarray(getattr(item, key), dtype=np.float32))
                if q.shape != p.shape:
                    continue
                scored.append((float(np.dot(p, q)), item.student_id, item.name))
            except Exception:
                continue
        scored.sort(reverse=True)
        return scored[0] if scored else (0.0, None, "")

    insight = nearest("insightface")
    facenet = nearest("facenet")
    insight_ok = insight[1] is not None and insight[0] >= INSIGHTFACE_THRESHOLD
    facenet_ok = facenet[1] is not None and facenet[0] >= FACENET_THRESHOLD
    same = insight[1] is not None and insight[1] == facenet[1]
    matched = bool(insight_ok and facenet_ok and same)
    return {
        "ok": True,
        "result": "MATCH" if matched else "UNKNOWN",
        "student_id": insight[1] if matched else None,
        "student_name": insight[2] if matched else None,
        "confidence": round(min(insight[0], facenet[0]) * 100, 2) if matched else None,
        "models_agree": bool(same),
        "checks": {
            "insightface_similarity": round(insight[0], 4),
            "insightface_pass": bool(insight_ok),
            "facenet_similarity": round(facenet[0], 4),
            "facenet_pass": bool(facenet_ok),
        },
        "bbox": probe["bbox"],
        "faces_detected": 1,
    }
