"""Face detection and SFace encoding using OpenCV's prebuilt runtime wheels."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

import cv2 as cv

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "data" / "models"
MODELS = {
    "detector": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "recognizer": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}


def _model_path(name: str) -> str:
    """Fetch OpenCV Zoo models once; they are cached outside source control."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    target = MODEL_DIR / Path(MODELS[name]).name
    if not target.exists():
        try:
            urlretrieve(MODELS[name], target)
        except Exception as error:
            raise RuntimeError(f"Could not download OpenCV {name} model: {error}") from error
    return str(target)


def _detector() -> cv.FaceDetectorYN:
    return cv.FaceDetectorYN.create(_model_path("detector"), "", (320, 320), 0.85, 0.3, 5000)


def _recognizer() -> cv.FaceRecognizerSF:
    return cv.FaceRecognizerSF.create(_model_path("recognizer"), "")


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
    encoding = _recognizer().feature(image, face)
    x, y, face_width, face_height = (int(value) for value in face[:4])
    return {"encoding": encoding, "box": {"top": y, "right": x + face_width, "bottom": y + face_height, "left": x}}


def face_distance(first: Any, candidate_path: str | Path) -> float:
    candidate = encode_largest_face(candidate_path)["encoding"]
    similarity = _recognizer().match(first, candidate, cv.FaceRecognizerSF_FR_COSINE)
    return max(0.0, 1.0 - float(similarity))
