"""Catalogue des elements."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_run_files(df: pd.DataFrame, run_dir: Path) -> dict[str, Path]:
    """Ecrit les fichiers du run."""
    data_path = run_dir / "data.csv"
    meta_path = run_dir / "meta.json"

    if data_path.exists() or meta_path.exists():
        raise FileExistsError("Fichiers de run deja presents.")

    df.to_csv(data_path, index=False)
    meta = {
        "rows": int(len(df)),
        "columns": list(df.columns),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

    return {"data": data_path, "meta": meta_path}
