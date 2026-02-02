"""Synchronisation du master catalog."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root

DEFAULT_MASTER_COLUMNS = [
    "doi",
    "isbn",
    "title",
    "year",
    "type",
    "authors",
    "keywords",
    "journal",
    "venue",
    "volume",
    "issue",
    "pages",
    "url",
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
    "file_hash",
    "primary_id",
    "fingerprint",
    "version",
    "replaced_by",
    "source",
    "added_at",
]

MANUAL_COLUMNS = ["file_hash", "source", "added_at", "collection", "pdf_path"]


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Ajoute les colonnes manquantes."""
    for name in columns:
        if name not in df.columns:
            df[name] = ""


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
        "isbn",
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


def load_master_catalog(path: Path | str) -> pd.DataFrame:
    """Charge le master catalog."""
    master_path = Path(path).expanduser()
    if master_path.exists():
        df = pd.read_csv(master_path)
    else:
        df = pd.DataFrame(columns=DEFAULT_MASTER_COLUMNS)
    _ensure_columns(df, DEFAULT_MASTER_COLUMNS)
    _ensure_columns(df, MANUAL_COLUMNS)
    return df


def upsert_manual_pdf_entry(
    df_master: pd.DataFrame,
    entry_dict: dict[str, Any],
    run_tag: str | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Met a jour une entree manuelle."""
    df_master = df_master.copy()
    _ensure_columns(df_master, MANUAL_COLUMNS)

    file_hash = str(entry_dict.get("file_hash", "")).strip()
    if not file_hash:
        return df_master, {"action": "error", "message": "MISSING_HASH"}

    hashes = df_master["file_hash"].fillna("").astype(str).str.strip()
    matches = hashes[hashes == file_hash].index.tolist()
    if matches:
        index = matches[0]
        updates = {
            "file_hash": file_hash,
            "source": entry_dict.get("source") or "manual",
            "added_at": entry_dict.get("added_at", ""),
            "collection": entry_dict.get("collection", ""),
            "pdf_path": entry_dict.get("pdf_path", ""),
        }
        for name, value in updates.items():
            if value is not None and str(value).strip():
                df_master.at[index, name] = value
        if "type" in entry_dict and "type" in df_master.columns:
            value = str(entry_dict.get("type", "")).strip()
            if value and _should_update_type(df_master.at[index, "type"]):
                df_master.at[index, "type"] = value
        if "isbn" in entry_dict and "isbn" in df_master.columns:
            value = str(entry_dict.get("isbn", "")).strip()
            if value and not str(df_master.at[index, "isbn"]).strip():
                df_master.at[index, "isbn"] = value
        if "doi" in entry_dict and "doi" in df_master.columns:
            value = str(entry_dict.get("doi", "")).strip()
            if value and not str(df_master.at[index, "doi"]).strip():
                df_master.at[index, "doi"] = value
        if "title" in entry_dict and "title" in df_master.columns:
            value = str(entry_dict.get("title", "")).strip()
            if value and not str(df_master.at[index, "title"]).strip():
                df_master.at[index, "title"] = value
        if "authors" in entry_dict and "authors" in df_master.columns:
            value = str(entry_dict.get("authors", "")).strip()
            if value and not str(df_master.at[index, "authors"]).strip():
                df_master.at[index, "authors"] = value
        if "keywords" in entry_dict and "keywords" in df_master.columns:
            value = str(entry_dict.get("keywords", "")).strip()
            if value and not str(df_master.at[index, "keywords"]).strip():
                df_master.at[index, "keywords"] = value
        if "year" in entry_dict and "year" in df_master.columns:
            value = str(entry_dict.get("year", "")).strip()
            if value and not str(df_master.at[index, "year"]).strip():
                df_master.at[index, "year"] = value
        if run_tag and "last_seen_run" in df_master.columns:
            df_master.at[index, "last_seen_run"] = run_tag
        return df_master, {"action": "updated", "index": int(index)}

    for name in entry_dict:
        if name not in df_master.columns:
            df_master[name] = ""
    new_record = {name: "" for name in df_master.columns}
    for name, value in entry_dict.items():
        new_record[name] = value
    new_record["source"] = entry_dict.get("source") or "manual"
    if run_tag and "last_seen_run" in df_master.columns:
        new_record["last_seen_run"] = run_tag

    df_master = pd.concat([df_master, pd.DataFrame([new_record])], ignore_index=True)
    return df_master, {"action": "created", "index": len(df_master) - 1}


def _should_update_type(current: Any) -> bool:
    """Indique si le type peut etre mis a jour."""
    text = str(current or "").strip().lower()
    return text in {"", "unknown", "inconnu"}


def upsert_scan_pdf_entry(
    df_master: pd.DataFrame,
    entry_dict: dict[str, Any],
    run_tag: str | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Met a jour une entree scannee."""
    df_master = df_master.copy()
    _ensure_columns(df_master, MANUAL_COLUMNS)

    file_hash = str(entry_dict.get("file_hash", "")).strip()
    pdf_path = str(entry_dict.get("pdf_path", "")).strip()
    if not file_hash and not pdf_path:
        return df_master, {"action": "error", "message": "MISSING_KEY"}

    match_index = None
    if file_hash and "file_hash" in df_master.columns:
        hashes = df_master["file_hash"].fillna("").astype(str).str.strip()
        matches = hashes[hashes == file_hash].index.tolist()
        if matches:
            match_index = matches[0]
    if match_index is None and pdf_path and "pdf_path" in df_master.columns:
        paths = df_master["pdf_path"].fillna("").astype(str).str.strip()
        matches = paths[paths == pdf_path].index.tolist()
        if matches:
            match_index = matches[0]

    if match_index is not None:
        updated = False
        if file_hash and "file_hash" in df_master.columns:
            if not str(df_master.at[match_index, "file_hash"]).strip():
                df_master.at[match_index, "file_hash"] = file_hash
                updated = True
        if pdf_path and "pdf_path" in df_master.columns:
            if str(df_master.at[match_index, "pdf_path"]).strip() != pdf_path:
                df_master.at[match_index, "pdf_path"] = pdf_path
                updated = True
        if "collection" in entry_dict and "collection" in df_master.columns:
            current = str(df_master.at[match_index, "collection"]).strip()
            value = str(entry_dict.get("collection", "")).strip()
            if value and (not current or current != value):
                df_master.at[match_index, "collection"] = value
                updated = True
        if "type" in entry_dict and "type" in df_master.columns:
            value = str(entry_dict.get("type", "")).strip()
            current = df_master.at[match_index, "type"]
            if value:
                if value == "book" and str(entry_dict.get("isbn", "")).strip():
                    df_master.at[match_index, "type"] = value
                    updated = True
                elif _should_update_type(current):
                    df_master.at[match_index, "type"] = value
                    updated = True
        if "isbn" in entry_dict and "isbn" in df_master.columns:
            value = str(entry_dict.get("isbn", "")).strip()
            if value and not str(df_master.at[match_index, "isbn"]).strip():
                df_master.at[match_index, "isbn"] = value
                updated = True
        if "doi" in entry_dict and "doi" in df_master.columns:
            value = str(entry_dict.get("doi", "")).strip()
            if value and not str(df_master.at[match_index, "doi"]).strip():
                df_master.at[match_index, "doi"] = value
                updated = True
        if "title" in entry_dict and "title" in df_master.columns:
            value = str(entry_dict.get("title", "")).strip()
            if value and not str(df_master.at[match_index, "title"]).strip():
                df_master.at[match_index, "title"] = value
                updated = True
        if "authors" in entry_dict and "authors" in df_master.columns:
            value = str(entry_dict.get("authors", "")).strip()
            if value and not str(df_master.at[match_index, "authors"]).strip():
                df_master.at[match_index, "authors"] = value
                updated = True
        if "keywords" in entry_dict and "keywords" in df_master.columns:
            value = str(entry_dict.get("keywords", "")).strip()
            if value and not str(df_master.at[match_index, "keywords"]).strip():
                df_master.at[match_index, "keywords"] = value
                updated = True
        if "year" in entry_dict and "year" in df_master.columns:
            value = str(entry_dict.get("year", "")).strip()
            if value and not str(df_master.at[match_index, "year"]).strip():
                df_master.at[match_index, "year"] = value
                updated = True
        if "source" in entry_dict and "source" in df_master.columns:
            current = str(df_master.at[match_index, "source"]).strip()
            value = str(entry_dict.get("source", "")).strip()
            if value and not current:
                df_master.at[match_index, "source"] = value
                updated = True
        if "added_at" in entry_dict and "added_at" in df_master.columns:
            current = str(df_master.at[match_index, "added_at"]).strip()
            value = str(entry_dict.get("added_at", "")).strip()
            if value and not current:
                df_master.at[match_index, "added_at"] = value
                updated = True
        if run_tag and "last_seen_run" in df_master.columns:
            df_master.at[match_index, "last_seen_run"] = run_tag
            updated = True
        return df_master, {"action": "updated" if updated else "existing", "index": int(match_index)}

    for name in entry_dict:
        if name not in df_master.columns:
            df_master[name] = ""
    new_record = {name: "" for name in df_master.columns}
    for name, value in entry_dict.items():
        new_record[name] = value
    if not new_record.get("source"):
        new_record["source"] = "library"
    if run_tag and "last_seen_run" in df_master.columns:
        new_record["last_seen_run"] = run_tag

    df_master = pd.concat([df_master, pd.DataFrame([new_record])], ignore_index=True)
    return df_master, {"action": "created", "index": len(df_master) - 1}
