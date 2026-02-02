"""Sources de donnees pour l app desktop."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader

from motherload_projet.library.master_catalog import load_master_catalog
from motherload_projet.library.paths import bibliotheque_root, library_root
from motherload_projet.workflow.uqar_proxy_queue import latest_to_be_downloaded


def count_pdfs(root: Path | None = None) -> int:
    """Compte les PDFs locaux."""
    base = root or (library_root() / "pdfs")
    if not base.exists():
        return 0
    return sum(1 for path in base.rglob("*.pdf") if path.is_file())


def count_master(master_path: Path | None = None) -> int:
    """Compte les entrees master."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = pd.read_csv(path)
    return len(df)


def _book_mask(df: pd.DataFrame) -> pd.Series:
    """Detecte les livres via type ou ISBN."""
    mask = pd.Series([False] * len(df))
    if "type" in df.columns:
        types = df["type"].fillna("").astype(str).str.lower().str.strip()
        base = types.isin({"book", "livre", "ouvrage"})
        mask = mask | base
        mask = mask | types.str.contains("book", na=False, regex=False)
        mask = mask | types.str.contains("livre", na=False, regex=False)
        mask = mask | types.str.contains("ouvrage", na=False, regex=False)

    isbn_cols = [col for col in df.columns if col.lower().startswith("isbn")]
    for col in isbn_cols:
        values = df[col].fillna("").astype(str).str.strip()
        mask = mask | (values != "")
    return mask


def _has_pdf_mask(df: pd.DataFrame) -> pd.Series:
    """Detecte les entrees avec PDF."""
    mask = pd.Series([False] * len(df))
    if "file_hash" in df.columns:
        hashes = df["file_hash"].fillna("").astype(str).str.strip()
        mask = mask | (hashes != "")
    if "pdf_path" in df.columns:
        paths = df["pdf_path"].fillna("").astype(str).str.strip()
        mask = mask | (paths != "")
    return mask


def _unknown_mask(df: pd.DataFrame) -> pd.Series:
    """Detecte les types inconnus."""
    if "type" not in df.columns:
        return pd.Series([True] * len(df))
    types = df["type"].fillna("").astype(str).str.lower().str.strip()
    return (types == "") | (types == "unknown") | (types == "inconnu")


def _unique_count(df: pd.DataFrame) -> int:
    """Compte unique par hash ou chemin."""
    if "file_hash" in df.columns:
        hashes = df["file_hash"].fillna("").astype(str).str.strip()
        hashed = hashes[hashes != ""]
        if not hashed.empty:
            return int(hashed.nunique())
    if "pdf_path" in df.columns:
        paths = df["pdf_path"].fillna("").astype(str).str.strip()
        return int(paths[paths != ""].nunique())
    return 0


def count_indexed_articles(master_path: Path | None = None) -> int:
    """Compte les articles indexes (avec PDF, hors livres)."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = load_master_catalog(path)
    mask = _has_pdf_mask(df) & ~_book_mask(df) & ~_unknown_mask(df)
    return _unique_count(df[mask])


def count_indexed_books(master_path: Path | None = None) -> int:
    """Compte les livres indexes (avec PDF)."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = load_master_catalog(path)
    mask = _has_pdf_mask(df) & _book_mask(df)
    return _unique_count(df[mask])


def count_indexed_unknown(master_path: Path | None = None) -> int:
    """Compte les documents inconnus (avec PDF)."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = load_master_catalog(path)
    mask = _has_pdf_mask(df) & _unknown_mask(df)
    return _unique_count(df[mask])


def count_references(master_path: Path | None = None) -> int:
    """Compte les references bibliographiques."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = load_master_catalog(path)
    return len(df)


def count_missing_pdfs(master_path: Path | None = None) -> int:
    """Compte les references sans PDF."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    if not path.exists():
        return 0
    df = load_master_catalog(path)
    mask = _has_pdf_mask(df)
    return int((~mask).sum())


def count_to_be_downloaded() -> int:
    """Compte les lignes a telecharger."""
    path = latest_to_be_downloaded(bibliotheque_root())
    if path is None:
        return 0
    df = pd.read_csv(path)
    return len(df)


def load_master_frame(master_path: Path | None = None) -> pd.DataFrame:
    """Charge le master catalog."""
    path = master_path or (bibliotheque_root() / "master_catalog.csv")
    df = load_master_catalog(path)
    return df.copy()


def search_master(df: pd.DataFrame, query: str, field: str) -> pd.DataFrame:
    """Filtre le master catalog."""
    text = (query or "").strip().lower()
    if not text:
        return df.head(0)
    candidates = {
        "title": "title",
        "doi": "doi",
        "authors": "authors",
        "year": "year",
        "keywords": "keywords",
        "collection": "collection",
        "pdf_path": "pdf_path",
    }
    if field != "all" and field not in candidates:
        return df.head(0)

    def _col_series(name: str) -> pd.Series:
        if name not in df.columns:
            return pd.Series([""] * len(df))
        return df[name].fillna("").astype(str)

    if field == "all":
        mask = pd.Series([False] * len(df))
        for col in candidates.values():
            series = _col_series(col).str.lower()
            mask = mask | series.str.contains(text, na=False, regex=False)
    else:
        series = _col_series(candidates[field]).str.lower()
        mask = series.str.contains(text, na=False, regex=False)
    return df[mask]


def search_pdfs_by_keyword(
    keyword: str,
    pdf_root: Path | None = None,
    max_pages: int = 2,
    progress_cb: Any | None = None,
) -> tuple[list[Path], list[str]]:
    """Recherche un mot-cle dans les PDFs."""
    text = (keyword or "").strip().lower()
    if not text:
        return [], []
    pdf_root = Path(pdf_root) if pdf_root else (library_root() / "pdfs")
    if not pdf_root.exists():
        return [], []
    pdfs = [path for path in pdf_root.rglob("*.pdf") if path.is_file()]
    total = len(pdfs)
    if progress_cb:
        progress_cb({"stage": "start", "total": total})

    matches: list[Path] = []
    errors: list[str] = []
    for index, pdf_path in enumerate(pdfs, start=1):
        if progress_cb:
            progress_cb({"stage": "item", "done": index, "total": total, "path": str(pdf_path)})
        try:
            reader = PdfReader(str(pdf_path))
            content_parts: list[str] = []
            for page in reader.pages[: max(1, max_pages)]:
                try:
                    content_parts.append(page.extract_text() or "")
                except Exception:
                    continue
            content = " ".join(content_parts).lower()
            if text in content:
                matches.append(pdf_path)
        except Exception as exc:
            errors.append(f"{pdf_path} | {exc}")
        time.sleep(0)

    if progress_cb:
        progress_cb({"stage": "done", "total": total, "matches": len(matches)})
    return matches, errors


def zotero_counts(zotero_root: Path) -> dict[str, Any]:
    """Retourne les compteurs Zotero."""
    db_path = Path(zotero_root).expanduser() / "zotero.sqlite"
    if not db_path.exists():
        return {"items": 0, "pdfs": 0, "error": "DB Zotero manquante"}

    try:
        conn = sqlite3.connect(
            f"file:{db_path.as_posix()}?mode=ro", uri=True, check_same_thread=False
        )
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.cursor()

        cursor.execute("SELECT itemTypeID, typeName FROM itemTypes")
        type_map = {row[0]: row[1] for row in cursor.fetchall()}
        excluded = {
            type_id
            for type_id, name in type_map.items()
            if name in {"attachment", "note", "annotation"}
        }
        if excluded:
            placeholders = ",".join("?" for _ in excluded)
            cursor.execute(
                f"SELECT COUNT(*) FROM items WHERE itemTypeID NOT IN ({placeholders})",
                tuple(excluded),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM items")
        items_count = int(cursor.fetchone()[0])

        cursor.execute("PRAGMA table_info(itemAttachments)")
        attach_cols = {row[1] for row in cursor.fetchall()}
        content_col = "contentType" if "contentType" in attach_cols else None
        if content_col is None and "mimeType" in attach_cols:
            content_col = "mimeType"

        pdf_count = 0
        if content_col:
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM itemAttachments
                WHERE {content_col} = 'application/pdf'
                """
            )
            pdf_count = int(cursor.fetchone()[0])
        elif "path" in attach_cols:
            cursor.execute(
                """
                SELECT COUNT(*) FROM itemAttachments
                WHERE path LIKE '%.pdf'
                """
            )
            pdf_count = int(cursor.fetchone()[0])

        conn.close()
        return {"items": items_count, "pdfs": pdf_count, "error": None}
    except sqlite3.Error as exc:
        return {"items": 0, "pdfs": 0, "error": str(exc)}
