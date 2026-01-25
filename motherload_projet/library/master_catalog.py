"""Synchronisation du master catalog."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root


def _unique_path(base: Path) -> Path:
    """Retourne un chemin unique."""
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = base.with_name(f"{base.stem}_{counter:02d}{base.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _timestamp_tag() -> str:
    """Genere un horodatage."""
    return datetime.now().strftime("%Y%m%d_%H%M")


def _normalize_doi(value: Any) -> str:
    """Normalise un DOI."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    lowered = text.lower()
    if lowered.startswith("https://doi.org/"):
        text = text[len("https://doi.org/") :]
    elif lowered.startswith("http://doi.org/"):
        text = text[len("http://doi.org/") :]
    elif lowered.startswith("doi:"):
        text = text[4:]
    return text.strip().lower()


def _normalize_text(value: Any) -> str:
    """Normalise un texte."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return " ".join(text.split()).lower()


def _catalog_key(doi: Any, title: Any, year: Any, fallback: int) -> str:
    """Genere une cle catalogue."""
    doi_norm = _normalize_doi(doi)
    if doi_norm:
        return f"doi:{doi_norm}"
    title_norm = _normalize_text(title)
    year_norm = _normalize_text(year)
    if title_norm or year_norm:
        return f"title_year:{title_norm}|{year_norm}"
    return f"unknown:{fallback}"


def _extract_tag(run_path: Path) -> str:
    """Extrait un tag depuis un run."""
    stem = run_path.stem
    if stem.startswith("bibliotheque_"):
        return stem[len("bibliotheque_") :]
    return _timestamp_tag()


def sync_catalog(run_bibliotheque_csv: Path | str) -> dict[str, Any]:
    """Synchronise le master catalog."""
    run_path = Path(run_bibliotheque_csv).expanduser()
    run_df = pd.read_csv(run_path)
    run_df = run_df.copy()

    required = [
        "doi",
        "title",
        "year",
        "status",
        "reason_code",
        "pdf_path",
        "final_url",
        "is_oa",
        "oa_status",
        "url_for_pdf",
        "last_http_status",
        "tried_methods",
        "collection",
    ]
    for name in required:
        if name not in run_df.columns:
            run_df[name] = ""

    master_path = ensure_dir(bibliotheque_root()) / "master_catalog.csv"
    if master_path.exists():
        master_df = pd.read_csv(master_path)
    else:
        master_df = pd.DataFrame(columns=run_df.columns)

    if "last_seen_run" not in master_df.columns:
        master_df["last_seen_run"] = ""

    for name in run_df.columns:
        if name not in master_df.columns:
            master_df[name] = ""

    master_records = master_df.to_dict(orient="records")
    key_map: dict[str, int] = {}
    for index, record in enumerate(master_records):
        key = _catalog_key(
            record.get("doi"), record.get("title"), record.get("year"), index
        )
        if key not in key_map:
            key_map[key] = index

    new_items = 0
    updated_items = 0
    last_seen = str(run_path)

    for index, row in run_df.iterrows():
        key = _catalog_key(row.get("doi"), row.get("title"), row.get("year"), index)
        row_dict = row.to_dict()
        if key in key_map:
            record = master_records[key_map[key]]
            old_status = str(record.get("status", "")).strip()
            new_status = str(row_dict.get("status", "")).strip()
            if old_status != new_status:
                updated_items += 1
            for name in [
                "status",
                "reason_code",
                "pdf_path",
                "final_url",
                "is_oa",
                "oa_status",
                "url_for_pdf",
                "last_http_status",
                "tried_methods",
                "collection",
            ]:
                record[name] = row_dict.get(name, "")
            record["last_seen_run"] = last_seen
            for name, value in row_dict.items():
                if name not in record or record.get(name, "") == "":
                    record[name] = value
        else:
            new_record: dict[str, Any] = {}
            for name in master_df.columns:
                new_record[name] = row_dict.get(name, "")
            for name, value in row_dict.items():
                if name not in new_record:
                    new_record[name] = value
            new_record["last_seen_run"] = last_seen
            master_records.append(new_record)
            key_map[key] = len(master_records) - 1
            new_items += 1

    master_df = pd.DataFrame(master_records)
    preferred = [
        "doi",
        "title",
        "year",
        "type",
        "authors",
        "keywords",
        "status",
        "reason_code",
        "pdf_path",
        "final_url",
        "is_oa",
        "oa_status",
        "url_for_pdf",
        "last_http_status",
        "tried_methods",
        "collection",
        "last_seen_run",
    ]
    ordered = [name for name in preferred if name in master_df.columns]
    ordered.extend([name for name in master_df.columns if name not in ordered])
    master_df = master_df[ordered]
    master_df.to_csv(master_path, index=False)

    reports_dir = ensure_dir(reports_root())
    diff_path = _unique_path(
        reports_dir / f"catalog_diff_{_extract_tag(run_path)}.txt"
    )
    diff_lines = [
        "Catalog diff",
        f"Nouveaux items: {new_items}",
        f"Items mis a jour: {updated_items}",
        f"Total master: {len(master_df)}",
        f"Master: {master_path}",
        f"Run: {run_path}",
    ]
    diff_path.write_text("\n".join(diff_lines) + "\n", encoding="utf-8")

    return {
        "master_path": master_path,
        "diff_path": diff_path,
        "new_items": new_items,
        "updated_items": updated_items,
        "total": len(master_df),
    }
