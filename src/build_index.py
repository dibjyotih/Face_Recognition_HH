"""Build a FAISS index from a consented social-post manifest."""
from __future__ import annotations

import argparse
from pathlib import Path

from .local_index import DEFAULT_INDEX, DEFAULT_METADATA, build_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="JSON array of consented post records")
    parser.add_argument("--index-path", default=str(DEFAULT_INDEX))
    parser.add_argument("--metadata-path", default=str(DEFAULT_METADATA))
    args = parser.parse_args()
    count = build_index(Path(args.manifest), Path(args.index_path), Path(args.metadata_path))
    print(f"Indexed {count} post images into {args.index_path}")


if __name__ == "__main__":
    main()
