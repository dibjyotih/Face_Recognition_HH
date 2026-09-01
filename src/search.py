"""Live Google Lens search and image-level face confirmation."""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from .faces import face_distance

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


@dataclass
class Match:
    title: str
    link: str
    image_url: str
    source: str
    platform: str | None
    distance: float | None
    raw: dict[str, Any]


def google_lens_search(source_image_url: str) -> list[dict[str, Any]]:
    key = os.environ.get("SERPAPI_API_KEY")
    if not key:
        raise RuntimeError("SERPAPI_API_KEY is required for the live Google Lens search")
    response = requests.get(SERPAPI_ENDPOINT, params={"engine": "google_lens", "url": source_image_url, "api_key": key}, timeout=60)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"Lens search failed: {data['error']}")
    # visual_matches are returned by the provider at runtime; no results are embedded here.
    return data.get("visual_matches", [])


def _download_image(url: str, destination: Path) -> bool:
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        image.save(destination, format="JPEG")
        return True
    except Exception:
        return False


SOCIAL_PLATFORMS = {
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "twitter.com": "X / Twitter",
    "x.com": "X / Twitter",
    "reddit.com": "Reddit",
}


def social_platform(url: str) -> str | None:
    url = url.lower()
    return next((name for domain, name in SOCIAL_PLATFORMS.items() if domain in url), None)


def find_confirmed_matches(
    encoding: Any,
    source_image_url: str,
    work_dir: Path,
    threshold: float = 0.60,
    social_only: bool = True,
) -> list[Match]:
    work_dir.mkdir(parents=True, exist_ok=True)
    candidates = google_lens_search(source_image_url)
    confirmed: list[Match] = []
    closest_distance: float | None = None
    for index, item in enumerate(candidates[:30]):
        image_url = item.get("thumbnail") or item.get("image") or ""
        link = item.get("link", "")
        platform = social_platform(link)
        if social_only and not platform:
            continue
        if not image_url:
            continue
        local_image = work_dir / f"candidate-{index}.jpg"
        distance = None
        if _download_image(image_url, local_image):
            try:
                distance = face_distance(encoding, local_image)
            except ValueError:
                pass
        if distance is not None:
            closest_distance = min(closest_distance, distance) if closest_distance is not None else distance
        if distance is not None and distance <= threshold:
            confirmed.append(Match(item.get("title", "Untitled result"), link, image_url, item.get("source", ""), platform, distance, item))
    if confirmed:
        return sorted(confirmed, key=lambda match: match.distance if match.distance is not None else 1.0)
    kind = "social-media" if social_only else "web"
    message = f"No face-confirmed {kind} result found"
    if closest_distance is not None:
        message += f"; closest candidate distance was {closest_distance:.3f} (threshold {threshold:.3f})"
    raise RuntimeError(message)
