"""Ingestion PDF manuelle via proxy UQAR."""

from __future__ import annotations

import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.config import get_manual_import_subdir
from motherload_projet.library.paths import (
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
    reports_root,
)
from motherload_projet.ui.collections_menu import choose_collection
from motherload_projet.data_mining.recuperation_article.run_unpaywall_batch import (
    _write_batch_outputs,
)

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
YEAR_PATTERN = re.compile(r"(19|20)\d{2}")


def _timestamp_tag() -> str:
    """Genere un horodatage."""
    return datetime.now().strftime("%Y%m%d_%H%M")


def _unique_path(base: Path) -> Path:
    """Retourne un chemin unique."""
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = base.with_name(f"{base.stem}_v{counter}{base.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _write_ingest_report(lines: list[str]) -> Path:
    """Ecrit le rapport ingest."""
    reports_dir = ensure_dir(reports_root())
    tag = _timestamp_tag()
    report_path = _unique_path(reports_dir / f"ingest_report_{tag}.txt")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _clean_text(value: Any) -> str:
    """Nettoie un champ texte."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return text


def _normalize_doi(value: Any) -> str:
    """Normalise un DOI."""
    text = _clean_text(value).lower()
    if not text:
        return ""
    if text.startswith("https://doi.org/"):
        text = text[len("https://doi.org/") :]
    elif text.startswith("http://doi.org/"):
        text = text[len("http://doi.org/") :]
    elif text.startswith("doi:"):
        text = text[4:]
    return text.strip()


def _normalize_text(value: Any) -> str:
    """Normalise un texte."""
    text = _clean_text(value).lower()
    return " ".join(text.split())


def _extract_pdf_text(path: Path, max_pages: int = 2) -> str:
    """Extrait du texte PDF (pages limitees)."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf manquant (pip install pypdf).") from exc
    reader = PdfReader(str(path))
    texts: list[str] = []
    page_count = min(len(reader.pages), max_pages)
    for index in range(page_count):
        try:
            page_text = reader.pages[index].extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            texts.append(page_text)
    return "\n".join(texts)


def _extract_doi_from_text(text: str) -> str | None:
    """Extrait un DOI depuis un texte."""
    if not text:
        return None
    match = DOI_PATTERN.search(text)
    if not match:
        return None
    doi = match.group(0).strip().lower()
    doi = doi.rstrip(").,;:]>\"' ")
    return doi or None


def extract_doi_from_pdf(path: Path | str) -> str | None:
    """Extrait un DOI depuis un PDF."""
    text = _extract_pdf_text(Path(path))
    return _extract_doi_from_text(text)


def sanitize_doi_for_filename(doi: str) -> str:
    """Sanitise un DOI pour un fichier."""
    cleaned = doi.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    return cleaned or "unknown"


def _extract_fallback_title_year(path: Path, text: str) -> tuple[str, str]:
    """Genere un titre/annee de fallback."""
    title = path.stem.replace("_", " ").replace("-", " ")
    year = ""
    for match in YEAR_PATTERN.finditer(text):
        year = match.group(0)
        break
    if not year:
        match = YEAR_PATTERN.search(title)
        if match:
            year = match.group(0)
    return title.strip(), year.strip()


def _match_by_doi(df: pd.DataFrame, doi: str) -> int | None:
    """Match par DOI."""
    if not doi or "doi" not in df.columns:
        return None
    doi_norm = _normalize_doi(doi)
    for index, value in df["doi"].items():
        if _normalize_doi(value) == doi_norm:
            return index
    return None


def _match_by_title_year(df: pd.DataFrame, title: str, year: str) -> int | None:
    """Match par titre + annee."""
    if "title" not in df.columns:
        return None
    title_norm = _normalize_text(title)
    if not title_norm:
        return None
    if "year" in df.columns and year:
        year_norm = _normalize_text(year)
        for index, row in df.iterrows():
            if (
                _normalize_text(row.get("title")) == title_norm
                and _normalize_text(row.get("year")) == year_norm
            ):
                return index
        return None
    for index, value in df["title"].items():
        if _normalize_text(value) == title_norm:
            return index
    return None


def match_record(
    doi: str | None,
    fallback_title_year: tuple[str, str] | None,
    proxy_queue_df: pd.DataFrame,
    run_df: pd.DataFrame,
) -> dict[str, Any] | None:
    """Trouve un record correspondant."""
    if doi:
        run_index = _match_by_doi(run_df, doi)
        if run_index is not None:
            return {"source": "run", "index": run_index}
        queue_index = _match_by_doi(proxy_queue_df, doi)
        if queue_index is not None:
            row = proxy_queue_df.loc[queue_index]
            run_index = _match_by_doi(run_df, row.get("doi", ""))
            if run_index is not None:
                return {"source": "run", "index": run_index}
            run_index = _match_by_title_year(
                run_df, row.get("title", ""), row.get("year", "")
            )
            if run_index is not None:
                return {"source": "run", "index": run_index}
    if fallback_title_year:
        title, year = fallback_title_year
        run_index = _match_by_title_year(run_df, title, year)
        if run_index is not None:
            return {"source": "run", "index": run_index}
        queue_index = _match_by_title_year(proxy_queue_df, title, year)
        if queue_index is not None:
            row = proxy_queue_df.loc[queue_index]
            run_index = _match_by_doi(run_df, row.get("doi", ""))
            if run_index is not None:
                return {"source": "run", "index": run_index}
    return None


def infer_run_csv_path(proxy_queue_path: Path | str) -> Path | None:
    """Devine le CSV bibliotheque associe."""
    proxy_queue_path = Path(proxy_queue_path).expanduser()
    stem = proxy_queue_path.stem
    tag = ""
    if stem.startswith("proxy_queue_"):
        tag = stem[len("proxy_queue_") :]
    if tag:
        candidate = bibliotheque_root() / f"bibliotheque_{tag}.csv"
        if candidate.exists():
            return candidate
    candidates = list(bibliotheque_root().glob("bibliotheque_*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _resolve_collection_path(value: Any) -> Path | None:
    """Resout un chemin de collection."""
    text = _clean_text(value)
    if not text:
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = collections_root() / candidate
    return candidate


def resolve_collection_for_ingest(
    proxy_queue_df: pd.DataFrame, run_df: pd.DataFrame
) -> Path | None:
    """Choisit la collection pour ingest."""
    values = []
    for df in (proxy_queue_df, run_df):
        if "collection" in df.columns:
            values.extend(df["collection"].tolist())
    unique = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        if text not in unique:
            unique.append(text)
    if len(unique) == 1:
        return _resolve_collection_path(unique[0])
    try:
        return choose_collection(collections_root())
    except KeyboardInterrupt:
        print("Annulé")
        return None


def manual_import_dir_for_collection(collection: Path) -> Path:
    """Retourne le dossier d import manuel."""
    pdfs_root = ensure_dir(library_root() / "pdfs")
    try:
        rel = collection.relative_to(collections_root())
    except ValueError:
        rel = Path(collection.name)
    manual_subdir = get_manual_import_subdir()
    return ensure_dir(pdfs_root / rel / manual_subdir)


def ingest_manual_pdfs(
    collection: Path,
    manual_import_dir: Path,
    proxy_queue_csv_path: Path | str,
    run_csv_path: Path | str,
) -> dict[str, Any]:
    """Ingere les PDFs manuels."""
    proxy_queue_csv_path = Path(proxy_queue_csv_path).expanduser()
    run_csv_path = Path(run_csv_path).expanduser()
    proxy_queue_df = (
        pd.read_csv(proxy_queue_csv_path) if proxy_queue_csv_path else pd.DataFrame()
    )
    run_df = pd.read_csv(run_csv_path)

    proxy_queue_df = proxy_queue_df.copy()
    for name in ["status", "reason_code", "pdf_path", "doi", "title", "year"]:
        if name not in proxy_queue_df.columns:
            proxy_queue_df[name] = ""
        proxy_queue_df[name] = proxy_queue_df[name].fillna("").astype(str)

    run_df = run_df.copy()
    if "doi" not in run_df.columns:
        run_df["doi"] = ""
    for name in [
        "status",
        "reason_code",
        "pdf_path",
        "final_url",
        "tried_methods",
    ]:
        if name not in run_df.columns:
            run_df[name] = ""
        run_df[name] = run_df[name].fillna("").astype(str)

    manual_import_dir = ensure_dir(manual_import_dir)
    pdf_files = sorted(
        [path for path in manual_import_dir.iterdir() if path.suffix.lower() == ".pdf"]
    )
    if not pdf_files:
        return {
            "status": "empty",
            "message": f"Aucun PDF dans {manual_import_dir}",
        }

    processed = 0
    matched = 0
    unmatched: list[str] = []
    errors: list[str] = []
    moved_paths: list[Path] = []
    start_time = time.monotonic()

    try:
        for path in pdf_files:
            processed += 1
            try:
                text = _extract_pdf_text(path)
                doi = _extract_doi_from_text(text)
            except RuntimeError as exc:
                return {"status": "error", "message": str(exc)}
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
                continue

            fallback_title_year = _extract_fallback_title_year(path, text)
            match = match_record(doi, fallback_title_year, proxy_queue_df, run_df)
            if match is None:
                unmatched.append(path.name)
                continue

            run_index = match["index"]
            doi_value = _normalize_doi(doi or run_df.at[run_index, "doi"])
            if not doi_value:
                unmatched.append(path.name)
                continue

            queue_index = None
            if not proxy_queue_df.empty:
                queue_index = _match_by_doi(proxy_queue_df, doi_value)
                if queue_index is None and fallback_title_year:
                    queue_index = _match_by_title_year(
                        proxy_queue_df, fallback_title_year[0], fallback_title_year[1]
                    )

            target_dir = manual_import_dir.parent
            target_path = target_dir / f"doi_{sanitize_doi_for_filename(doi_value)}.pdf"
            target_path = _unique_path(target_path)
            try:
                shutil.move(str(path), str(target_path))
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
                continue

            moved_paths.append(target_path)
            matched += 1
            run_df.at[run_index, "status"] = "downloaded"
            run_df.at[run_index, "reason_code"] = "PROXY_MANUAL"
            run_df.at[run_index, "pdf_path"] = str(target_path)
            run_df.at[run_index, "final_url"] = "uqar_proxy_manual"
            if "tried_methods" in run_df.columns:
                run_df.at[run_index, "tried_methods"] = "uqar_proxy_manual"
            if queue_index is not None:
                proxy_queue_df.at[queue_index, "status"] = "downloaded"
                proxy_queue_df.at[queue_index, "reason_code"] = "PROXY_MANUAL"
                proxy_queue_df.at[queue_index, "pdf_path"] = str(target_path)
    except KeyboardInterrupt:
        errors.append("Annule par l utilisateur.")

    if not proxy_queue_df.empty:
        try:
            proxy_queue_df.to_csv(proxy_queue_csv_path, index=False)
        except Exception as exc:
            errors.append(f"proxy_queue update: {exc}")

    duration_sec = time.monotonic() - start_time
    avg_rate = (processed / duration_sec) if duration_sec > 0 else 0.0

    (
        bibliotheque_path,
        to_be_downloaded_path,
        report_path,
        catalog_result,
    ) = _write_batch_outputs(
        run_df, "doi", "Rapport UQAR proxy ingest", duration_sec, avg_rate
    )

    ingest_lines = [
        "UQAR proxy ingest report",
        f"Proxy queue: {proxy_queue_csv_path}",
        f"Run source: {run_csv_path}",
        f"Collection: {collection}",
        f"Manual import: {manual_import_dir}",
        f"PDFs trouves: {len(pdf_files)}",
        f"Ingeres: {matched}",
        f"Inconnus: {len(unmatched)}",
        f"Erreurs: {len(errors)}",
        f"Duree: {duration_sec:.1f}s",
    ]
    if moved_paths:
        ingest_lines.append("PDFs ingeres:")
        for path in moved_paths:
            ingest_lines.append(f"- {path}")
    ingest_lines.append("PDFs inconnus:")
    if unmatched:
        for name in unmatched:
            ingest_lines.append(f"- {name}")
    else:
        ingest_lines.append("- aucun")
    if errors:
        ingest_lines.append("Erreurs:")
        for line in errors:
            ingest_lines.append(f"- {line}")

    ingest_report_path = _write_ingest_report(ingest_lines)
    report_path.write_text(
        report_path.read_text(encoding="utf-8")
        + "\n".join(ingest_lines)
        + "\n",
        encoding="utf-8",
    )

    return {
        "status": "ok",
        "processed": processed,
        "matched": matched,
        "unmatched": len(unmatched),
        "errors": len(errors),
        "bibliotheque_path": bibliotheque_path,
        "to_be_downloaded_path": to_be_downloaded_path,
        "report_path": report_path,
        "ingest_report_path": ingest_report_path,
        "catalog_diff": catalog_result["diff_path"],
        "moved_paths": moved_paths,
    }
