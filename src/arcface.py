"""ArcFace embeddings with ONNX Runtime and OpenCV's YuNet face detector."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve
from zipfile import ZipFile

import cv2 as cv
import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "data" / "models"
YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
BUFFALO_L_URL = "https://github.com/face-analysis/insightface/releases/download/v0.7/buffalo_l.zip"
TEMPLATE_112 = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32,
)


@lru_cache(maxsize=1)
def _detector() -> cv.FaceDetectorYN:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    yunet = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
    if not yunet.exists():
        try:
            urlretrieve(YUNET_URL, yunet)
        except Exception as error:
            raise RuntimeError(f"Could not download face detector model: {error}") from error
    return cv.FaceDetectorYN.create(str(yunet), "", (320, 320), 0.85, 0.3, 5000)


def _arcface_path() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    arcface = MODEL_DIR / "w600k_r50.onnx"
    if arcface.exists():
        return arcface
    archive = MODEL_DIR / "buffalo_l.zip"
    try:
        urlretrieve(BUFFALO_L_URL, archive)
        with ZipFile(archive) as bundle:
            with bundle.open("w600k_r50.onnx") as source, arcface.open("wb") as destination:
                destination.write(source.read())
    except Exception as error:
        raise RuntimeError(f"Could not download or extract ArcFace model: {error}") from error
    finally:
        archive.unlink(missing_ok=True)
    return arcface


@lru_cache(maxsize=1)
def _session() -> ort.InferenceSession:
    return ort.InferenceSession(str(_arcface_path()), providers=["CPUExecutionProvider"])


def _embedding(image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    transform, _ = cv.estimateAffinePartial2D(landmarks, TEMPLATE_112, method=cv.LMEDS)
    if transform is None:
        raise ValueError("Could not align detected face")
    aligned = cv.warpAffine(image, transform, (112, 112), borderValue=0.0)
    rgb = cv.cvtColor(aligned, cv.COLOR_BGR2RGB).astype(np.float32)
    blob = np.transpose((rgb - 127.5) / 127.5, (2, 0, 1))[np.newaxis, ...]
    session = _session()
    output = session.run(None, {session.get_inputs()[0].name: blob})[0].reshape(-1).astype(np.float32)
    return output / np.linalg.norm(output)


def encode_largest_face(image_path: str | Path) -> dict[str, Any]:
    image = cv.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image {image_path}")
    height, width = image.shape[:2]
    detector = _detector()
    detector.setInputSize((width, height))
    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        raise ValueError(f"No face detected in {image_path}")
    face = max(faces, key=lambda item: float(item[2] * item[3]))
    embedding = _embedding(image, np.asarray(face[4:14], dtype=np.float32).reshape(5, 2))
    left, top, face_width, face_height = (int(value) for value in face[:4])
    return {"encoding": embedding, "box": {"top": top, "right": left + face_width, "bottom": top + face_height, "left": left}}


def face_distance(first: Any, candidate_path: str | Path) -> float:
    candidate = encode_largest_face(candidate_path)["encoding"]
    return max(0.0, 1.0 - float(np.dot(first, candidate)))
