"""Minimal public image upload used only so Google Lens can fetch a camera frame."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import requests


def upload_to_imgbb(image_path: str | Path) -> str:
    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise RuntimeError("IMGBB_API_KEY is required for --camera. Add it to .env or supply --source-url.")
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    response = requests.post("https://api.imgbb.com/1/upload", data={"key": api_key, "image": encoded}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"Image upload failed: {payload}")
    return payload["data"]["url"]
