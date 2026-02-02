"""Rapports d'ecarts de catalogues."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.catalogs.scoring import CompletenessConfig, is_complete


def _has_pdf_mask(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series([False] * len(df))
    if "pdf_path" in df.columns:
        paths = df["pdf_path"].fillna("").astype(str).str.strip()
        mask = mask | (paths != "")
    if "file_hash" in df.columns:
        hashes = df["file_hash"].fillna("").astype(str).str.strip()
        mask = mask | (hashes != "")
    return mask


def refs_without_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """References sans PDF."""
    mask = ~_has_pdf_mask(df)
    return df[mask].copy()


def refs_incomplete(df: pd.DataFrame, cfg: CompletenessConfig) -> pd.DataFrame:
    """References incompletes."""
    rows = []
    for _, row in df.iterrows():
        if not is_complete(row.to_dict(), cfg):
            rows.append(row)
    if not rows:
        return df.head(0).copy()
    return pd.DataFrame(rows)


def pdfs_without_ref(df: pd.DataFrame, pdf_paths: list[str]) -> pd.DataFrame:
    """PDFs sans reference."""
    master_paths = set(
        df.get("pdf_path", pd.Series([], dtype=str)).fillna("").astype(str).str.strip()
    )
    orphans = [path for path in pdf_paths if path not in master_paths]
    return pd.DataFrame({"pdf_path": orphans})


def duplicates_and_replacements(df: pd.DataFrame) -> pd.DataFrame:
    """Detecte doublons et remplacements."""
    records: list[dict[str, Any]] = []
    if "primary_id" in df.columns:
        counts = df["primary_id"].fillna("").astype(str).str.strip().value_counts()
        duplicates = counts[counts > 1].index.tolist()
        for pid in duplicates:
            rows = df[df["primary_id"].astype(str).str.strip() == pid]
            for _, row in rows.iterrows():
                item = row.to_dict()
                item["issue"] = "duplicate_primary_id"
                records.append(item)
    if "replaced_by" in df.columns:
        replaced = df[df["replaced_by"].fillna("").astype(str).str.strip() != ""]
        for _, row in replaced.iterrows():
            item = row.to_dict()
            item["issue"] = "replaced_by"
            records.append(item)
    if not records:
        return df.head(0).copy()
    return pd.DataFrame(records)


def write_reports(
    master_df: pd.DataFrame,
    pdf_paths: list[str],
    output_dir: Path,
    cfg: CompletenessConfig,
) -> dict[str, str]:
    """Ecrit les rapports CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    refs_no_pdf = refs_without_pdf(master_df)
    pdfs_no_ref = pdfs_without_ref(master_df, pdf_paths)
    refs_inc = refs_incomplete(master_df, cfg)
    dups = duplicates_and_replacements(master_df)

    paths = {
        "refs_without_pdf": output_dir / "refs_without_pdf.csv",
        "pdfs_without_ref": output_dir / "pdfs_without_ref.csv",
        "refs_incomplete": output_dir / "refs_incomplete.csv",
        "duplicates_and_replacements": output_dir / "duplicates_and_replacements.csv",
    }
    refs_no_pdf.to_csv(paths["refs_without_pdf"], index=False)
    pdfs_no_ref.to_csv(paths["pdfs_without_ref"], index=False)
    refs_inc.to_csv(paths["refs_incomplete"], index=False)
    dups.to_csv(paths["duplicates_and_replacements"], index=False)

    return {name: str(path) for name, path in paths.items()}
