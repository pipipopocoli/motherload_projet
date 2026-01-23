"""Gestion des instantanes de bibliotheque."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def create_run_dir(collection_dir: Path) -> Path:
    """Cree un dossier de run unique."""
    runs_dir = collection_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    base_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = runs_dir / base_name
    counter = 1
    while run_dir.exists():
        run_dir = runs_dir / f"{base_name}_{counter:02d}"
        counter += 1

    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir
