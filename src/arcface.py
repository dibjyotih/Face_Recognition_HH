"""ArcFace face detection and normalized embeddings via InsightFace."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2 as cv
import numpy as np
from insightface.app import FaceAnalysis


@lru_cache(maxsize=1)
def app() -> FaceAnalysis:
    # InsightFace downloads the Buffalo-L detector/ArcFace model on first use.
    model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    model.prepare(ctx_id=0, det_size=(640, 640))
    return model


def encode_largest_face(image_path: str | Path) -> dict[str, Any]:
    image = cv.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image {image_path}")
    faces = app().get(image)
    if not faces:
        raise ValueError(f"No face detected in {image_path}")
    face = max(faces, key=lambda item: float(item.bbox[2] - item.bbox[0]) * float(item.bbox[3] - item.bbox[1]))
    embedding = np.asarray(face.normed_embedding, dtype=np.float32)
    left, top, right, bottom = (int(value) for value in face.bbox)
    return {"encoding": embedding, "box": {"top": top, "right": right, "bottom": bottom, "left": left}}


def face_distance(first: Any, candidate_path: str | Path) -> float:
    candidate = encode_largest_face(candidate_path)["encoding"]
    return max(0.0, 1.0 - float(np.dot(first, candidate)))
