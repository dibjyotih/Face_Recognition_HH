"""Interactive webcam capture used by the face-search pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import cv2 as cv


def capture_face_image(destination_dir: Path, camera_index: int = 0) -> Path:
    camera = cv.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError("Could not open the webcam. Check camera permissions or pass --camera-index.")
    window = "Face scan - SPACE capture | Q cancel"
    print("Camera open. Look at the camera, press SPACE to capture, or Q to cancel.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Could not read a frame from the webcam")
            cv.imshow(window, frame)
            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                raise RuntimeError("Camera capture cancelled")
            if key == ord(" "):
                destination_dir.mkdir(parents=True, exist_ok=True)
                name = f"face-scan-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jpg"
                path = destination_dir / name
                if not cv.imwrite(str(path), frame):
                    raise RuntimeError("Could not save the captured image")
                return path
    finally:
        camera.release()
        cv.destroyAllWindows()
