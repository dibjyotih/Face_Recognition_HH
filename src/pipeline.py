"""Face scan -> live reverse-image discovery -> on-chain content anchor / verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .faces import encode_largest_face
from .camera import capture_face_image
from .search import Match, find_confirmed_matches
from .upload import upload_to_imgbb

ROOT = Path(__file__).resolve().parents[1]


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def fingerprint(match: Any) -> tuple[str, dict[str, Any]]:
    metadata = {
        "schema": "face-web-chain/v1",
        "content_type": "social_or_web_post",
        "source": match.source,
        "platform": match.platform,
        "post_url": match.link,
        "title": match.title,
        "matched_image_url": match.image_url,
        "face_distance": match.distance,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }
    digest = hashlib.sha256(canonical_bytes(metadata)).hexdigest()
    return "0x" + digest, metadata


def node_json(arguments: list[str]) -> dict[str, Any]:
    process = subprocess.run(["node", *arguments], cwd=ROOT, text=True, capture_output=True)
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip())
    return json.loads(process.stdout)


def append_evidence(path: Path, metadata: dict[str, Any]) -> int:
    """Append to a valid JSON array, migrating the original one-record format."""
    records: list[dict[str, Any]] = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        records = existing if isinstance(existing, list) else [existing]
    records.append(metadata)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return len(records) - 1


def choose_match(matches: list[Match], selected: int | None) -> Match:
    print("\nFace-confirmed social-media results:")
    for index, match in enumerate(matches, start=1):
        print(f"[{index}] {match.platform} | distance {match.distance:.3f} | {match.title}\n    {match.link}")
    if selected is None:
        while True:
            answer = input(f"Select a post to anchor (1-{len(matches)}, or q to cancel): ").strip().lower()
            if answer == "q":
                raise RuntimeError("No post selected")
            if answer.isdigit() and 1 <= int(answer) <= len(matches):
                return matches[int(answer) - 1]
            print("Enter a displayed number or q.")
    if not 1 <= selected <= len(matches):
        raise ValueError(f"--select must be between 1 and {len(matches)}")
    return matches[selected - 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", help="Local input face image")
    parser.add_argument("--source-url", help="Public HTTPS URL for the same source image")
    parser.add_argument("--camera", action="store_true", help="Capture the input image directly from a webcam")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--include-web", action="store_true", help="Also list non-social web pages returned by Lens")
    parser.add_argument("--select", type=int, help="Select a numbered result non-interactively")
    parser.add_argument("--uri", default="", help="Optional IPFS CID or immutable evidence URI")
    parser.add_argument("--verify-only", metavar="METADATA_JSON", help="Recompute and verify a saved evidence file")
    parser.add_argument("--evidence-index", type=int, default=-1, help="Array entry to verify; -1 selects the newest record")
    parser.add_argument("--threshold", type=float, default=0.60)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")

    if args.verify_only:
        saved = json.loads(Path(args.verify_only).read_text(encoding="utf-8"))
        records = saved if isinstance(saved, list) else [saved]
        try:
            metadata = records[args.evidence_index]
        except IndexError as error:
            raise ValueError(f"--evidence-index must be between 0 and {len(records) - 1}") from error
        content_hash = "0x" + hashlib.sha256(canonical_bytes(metadata)).hexdigest()
        result = node_json(["scripts/verify.js", content_hash])
        print(json.dumps({"record_index": args.evidence_index % len(records), "hash": content_hash, "chain_record": result, "verified": result["found"]}, indent=2))
        return

    if args.camera and args.image:
        parser.error("Use either --camera or --image, not both")
    if not args.camera and not args.image:
        parser.error("Provide --camera or --image")
    image_path = capture_face_image(ROOT / "data" / "captures", args.camera_index) if args.camera else Path(args.image)
    source_url = args.source_url or upload_to_imgbb(image_path)
    face = encode_largest_face(image_path)
    print(f"Detected face at {face['box']}; generated a 128-D encoding. Searching Google Lens...")
    matches = find_confirmed_matches(face["encoding"], source_url, ROOT / "data" / "candidates", args.threshold, not args.include_web)
    match = choose_match(matches, args.select)
    content_hash, metadata = fingerprint(match)
    evidence = ROOT / "data" / "evidence.json"
    evidence_index = append_evidence(evidence, metadata)
    print(json.dumps({"face_confirmed": True, "distance": match.distance, "post_url": match.link, "fingerprint": content_hash}, indent=2))
    anchor = node_json(["scripts/register.js", content_hash, args.uri])
    verification = node_json(["scripts/verify.js", content_hash])
    print(json.dumps({"anchor": anchor, "verification": verification, "evidence_file": str(evidence), "evidence_index": evidence_index}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"PIPELINE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
