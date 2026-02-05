"""Export des catalogues et BibTeX."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.catalogs.scoring import first_author_last


def _safe_text(value: Any) -> str:
    """Nettoie un champ pour BibTeX."""
    if value is None:
        return ""
    text = str(value).strip()
    return text.replace("{", "").replace("}", "")


def _format_authors(authors: Any) -> str:
    """Formate les auteurs pour BibTeX."""
    if not authors:
        return ""
    text = str(authors).strip()
    if not text:
        return ""
    if ";" in text:
        parts = [part.strip() for part in text.split(";") if part.strip()]
    elif " and " in text:
        parts = [part.strip() for part in text.split(" and ") if part.strip()]
    else:
        parts = [text]
    formatted: list[str] = []
    for part in parts:
        if "," in part:
            formatted.append(part)
        else:
            tokens = [token for token in part.split() if token]
            if len(tokens) >= 2:
                last = tokens[-1]
                first = " ".join(tokens[:-1])
                formatted.append(f"{last}, {first}")
            else:
                formatted.append(part)
    return " and ".join(formatted)


def _citekey_base(row: pd.Series) -> str:
    """Cree la base du citekey."""
    author = first_author_last(row.get("authors"))
    year = str(row.get("year", "")).strip() or "0000"
    safe_author = "".join(ch for ch in author if ch.isalnum()) or "Unknown"
    return f"{safe_author}_{year}"


def assign_citekeys(df: pd.DataFrame) -> list[str]:
    """Assigne des citekeys stables."""
    used: dict[str, int] = {}
    keys: list[str] = []
    for _, row in df.iterrows():
        base = _citekey_base(row)
        if base not in used:
            used[base] = 1
            keys.append(base)
        else:
            used[base] += 1
            keys.append(f"{base}_{used[base]}")
    return keys


def export_bibtex(df: pd.DataFrame, path: Path) -> Path:
    """Exporte un BibTeX."""
    df = df.copy()
    citekeys = assign_citekeys(df)
    lines: list[str] = []
    for index, row in df.iterrows():
        doc_type = str(row.get("type", "")).strip().lower()
        if doc_type == "book":
            entry_type = "book"
        elif doc_type == "article":
            entry_type = "article"
        else:
            entry_type = "misc"
        key = citekeys[index]
        fields = {
            "title": _safe_text(row.get("title", "")),
            "author": _format_authors(row.get("authors", "")),
            "year": _safe_text(row.get("year", "")),
            "doi": _safe_text(row.get("doi", "")),
            "isbn": _safe_text(row.get("isbn", "")),
            "journal": _safe_text(row.get("journal", "") or row.get("venue", "")),
            "volume": _safe_text(row.get("volume", "")),
            "number": _safe_text(row.get("issue", "")),
            "pages": _safe_text(row.get("pages", "")),
            "url": _safe_text(row.get("url", "")),
        }
        lines.append(f"@{entry_type}{{{key},")
        for name, value in fields.items():
            if value:
                lines.append(f"  {name} = {{{value}}},")
        lines.append("}\n")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_catalog(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    """Exporte CSV + JSON."""
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)


def export_catalogs(
    master_df: pd.DataFrame,
    complete_df: pd.DataFrame,
    output_dir: Path,
) -> dict[str, str]:
    """Exporte les catalogues."""
    output_dir.mkdir(parents=True, exist_ok=True)
    master_csv = output_dir / "master_catalog.csv"
    master_json = output_dir / "master_catalog.json"
    complete_csv = output_dir / "complete_catalog.csv"
    complete_json = output_dir / "complete_catalog.json"
    export_catalog(master_df, master_csv, master_json)
    export_catalog(complete_df, complete_csv, complete_json)
    return {
        "master_csv": str(master_csv),
        "master_json": str(master_json),
        "complete_csv": str(complete_csv),
        "complete_json": str(complete_json),
    }
