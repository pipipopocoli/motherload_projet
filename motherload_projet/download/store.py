"""Stockage PDF."""

from __future__ import annotations

import re
from pathlib import Path

from motherload_projet.library.paths import collections_root, ensure_dir, library_root


def _sanitize_doi(doi: str) -> str:
    cleaned = doi.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    return cleaned or "unknown"


def store_pdf_bytes(collection: Path, doi: str, pdf_bytes: bytes) -> Path:
    """Stocke un PDF localement."""
    pdfs_root = ensure_dir(library_root() / "pdfs")
    try:
        collection_rel = collection.relative_to(collections_root())
    except ValueError:
        collection_rel = Path(collection.name)
    target_dir = ensure_dir(pdfs_root / collection_rel)
    target_path = target_dir / f"doi_{_sanitize_doi(doi)}.pdf"
    target_path.write_bytes(pdf_bytes)
    return target_path
