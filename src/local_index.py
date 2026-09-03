"""FAISS indexing and querying for consented social-post images."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from .arcface import encode_largest_face
from .search import Match

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "data" / "face_index.faiss"
DEFAULT_METADATA = ROOT / "data" / "face_index_metadata.json"


def build_index(manifest_path: Path, index_path: Path = DEFAULT_INDEX, metadata_path: Path = DEFAULT_METADATA) -> int:
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("The post manifest must be a non-empty JSON array")
    embeddings: list[np.ndarray] = []
    indexed_records: list[dict[str, Any]] = []
    for record in records:
        for field in ("id", "platform", "post_url", "title", "image_path"):
            if not record.get(field):
                raise ValueError(f"Post manifest entry is missing '{field}'")
        image_path = Path(record["image_path"])
        if not image_path.is_absolute():
            image_path = ROOT / image_path
        encoded = encode_largest_face(image_path)["encoding"]
        indexed_records.append({**record, "image_path": str(image_path)})
        embeddings.append(encoded)
    vectors = np.ascontiguousarray(np.vstack(embeddings), dtype=np.float32)
    index = faiss.IndexFlatIP(vectors.shape[1])  # ArcFace embeddings are L2-normalized.
    index.add(vectors)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    metadata_path.write_text(json.dumps(indexed_records, indent=2), encoding="utf-8")
    return len(indexed_records)


def search_index(
    query_embedding: np.ndarray,
    index_path: Path = DEFAULT_INDEX,
    metadata_path: Path = DEFAULT_METADATA,
    threshold: float = 0.45,
    limit: int = 10,
) -> list[Match]:
    if not index_path.exists() or not metadata_path.exists():
        raise RuntimeError("Local index is missing. Run: python -m src.build_index --manifest .\\data\\posts.json")
    index = faiss.read_index(str(index_path))
    records = json.loads(metadata_path.read_text(encoding="utf-8"))
    scores, identifiers = index.search(np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32), min(limit, index.ntotal))
    matches: list[Match] = []
    for score, identifier in zip(scores[0], identifiers[0]):
        if identifier < 0:
            continue
        distance = max(0.0, 1.0 - float(score))
        if distance > threshold:
            continue
        record = records[int(identifier)]
        matches.append(Match(record["title"], record["post_url"], record["image_path"], record["platform"], record["platform"], distance, record))
    if not matches:
        raise RuntimeError(f"No local face match met the distance threshold {threshold:.3f}")
    return matches
