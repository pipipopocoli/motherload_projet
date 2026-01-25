"""Workflow Unpaywall batch."""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from motherload_projet.download.fetcher import fetch_url
from motherload_projet.download.html_harvest import extract_pdf_urls_from_html
from motherload_projet.download.pdf_validate import validate_pdf_bytes
from motherload_projet.download.store import store_pdf_bytes
from motherload_projet.library.paths import (
    archives_root,
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
    reports_root,
)
from motherload_projet.library.master_catalog import sync_catalog
from motherload_projet.oa.resolver import resolve_pdf_urls_from_unpaywall
from motherload_projet.ui.collections_menu import choose_collection

DEFAULT_MIN_PDF_KB = 100
DEFAULT_PROGRESS_EVERY = 10
PROGRESS_WINDOW = 10


def _timestamp_tag() -> str:
    """Genere un horodatage."""
    return datetime.now().strftime("%Y%m%d_%H%M")


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


def _archive_old_downloads(
    bib_root: Path, archives_dir: Path, keep_path: Path
) -> list[Path]:
    """Archive les anciens to_be_downloaded."""
    archives_dir = ensure_dir(archives_dir)
    archived: list[Path] = []
    for path in bib_root.glob("to_be_downloaded_*.csv"):
        if path.resolve() == keep_path.resolve():
            continue
        target = _unique_path(archives_dir / path.name)
        path.replace(target)
        archived.append(target)
    return archived


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    """Trouve une colonne par priorite."""
    lower_map = {column.lower(): column for column in columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


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
    return text.strip()


def _normalize_type(value: Any) -> str:
    """Normalise un type."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "article"
    text = str(value).strip()
    return text or "article"


def _format_doi(value: Any, index: int) -> str:
    """Formate un DOI pour rapport."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return f"<manquant:{index}>"
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return f"<manquant:{index}>"
    return text


def _format_eta(seconds: float) -> str:
    """Formate un ETA."""
    if seconds <= 0:
        return "00:00:00"
    total = int(seconds + 0.5)
    minutes, sec = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


def _parse_bool(value: Any) -> bool | None:
    """Parse un booleen."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text or text == "nan":
        return None
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _short_title(title: Any, max_len: int = 40) -> str:
    """Raccourcit un titre."""
    text = str(title or "").strip()
    if not text:
        return "-"
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def _progress_metrics(
    done: int, total: int, ok_count: int, fail_count: int, durations: list[float]
) -> tuple[float, str, float]:
    """Calcule les metrics de progression."""
    avg_item = (sum(durations) / len(durations)) if durations else 0.0
    items_per_sec = (1.0 / avg_item) if avg_item > 0 else 0.0
    if done < 2 or avg_item <= 0:
        eta_text = "estimating..."
    else:
        eta_text = _format_eta(avg_item * max(total - done, 0))
    rate = (ok_count / done) if done > 0 else 0.0
    return items_per_sec, eta_text, rate


def _progress_line(
    done: int, total: int, ok_count: int, fail_count: int, durations: list[float]
) -> str:
    """Construit une ligne de progression."""
    items_per_sec, eta_text, rate = _progress_metrics(
        done, total, ok_count, fail_count, durations
    )
    return (
        f"Progression: {done}/{total} "
        f"OK {ok_count} FAIL {fail_count} ({rate:.1%}) | "
        f"{items_per_sec:.2f} items/s | ETA {eta_text}"
    )


def _verbose_item_line(
    done: int,
    total: int,
    doi: str,
    status: str,
    reason: str,
    method: str,
    elapsed: float,
    bytes_len: int | None,
    ok_count: int,
    fail_count: int,
    durations: list[float],
) -> str:
    """Construit une ligne detaillee."""
    items_per_sec, eta_text, rate = _progress_metrics(
        done, total, ok_count, fail_count, durations
    )
    bytes_value = bytes_len if bytes_len is not None else 0
    method_value = method or "-"
    return (
        f"[{done}/{total}] DOI={doi} -> "
        f"status={status} reason={reason} "
        f"(t={elapsed:.1f}, bytes={bytes_value}) method={method_value} | "
        f"OK {ok_count} FAIL {fail_count} ({rate:.1%}) | "
        f"{items_per_sec:.2f} items/s | ETA {eta_text}"
    )


def _ensure_str_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Force des colonnes en str."""
    for name in columns:
        if name in df.columns:
            df[name] = df[name].fillna("").astype(str)


def _print_compact_progress(line: str, previous_len: int) -> int:
    """Affiche une progression compacte."""
    padded = line.ljust(previous_len)
    print(f"\r{padded}", end="", flush=True)
    return len(padded)


def _collection_label(collection: Path) -> str:
    """Formate un label de collection."""
    try:
        return str(collection.relative_to(collections_root()))
    except ValueError:
        return str(collection)


def _resolve_collection_path(value: Any, fallback: Path | None) -> Path | None:
    """Resout un chemin de collection."""
    if value is not None:
        text = str(value).strip()
        if text and text.lower() != "nan":
            candidate = Path(text)
            if not candidate.is_absolute():
                candidate = collections_root() / candidate
            return candidate
    return fallback


def _mark_unprocessed_as_error(df: pd.DataFrame) -> None:
    """Marque les lignes non traitees."""
    if "status" not in df.columns or "reason_code" not in df.columns:
        return
    mask = df["status"].astype(str).str.strip() == ""
    df.loc[mask, "status"] = "failed"
    df.loc[mask, "reason_code"] = "ERROR"


def _is_html_content(content_type: str, content: bytes) -> bool:
    """Detecte un contenu HTML."""
    if "html" in content_type.lower():
        return True
    head = content[:2048].lower()
    return b"<html" in head or b"<!doctype html" in head


def _map_fetch_failure(status_code: int, error_code: str | None) -> str:
    """Mappe un echec HTTP."""
    if error_code == "TIMEOUT":
        return "TIMEOUT"
    if status_code == 403:
        return "HTTP_403"
    if status_code == 429:
        return "HTTP_429"
    return "ERROR"


def _map_validation_code(code: str) -> str:
    """Mappe une validation PDF."""
    return "ERROR"


def _write_batch_outputs(
    df: pd.DataFrame,
    doi_column: str,
    report_title: str,
    duration_sec: float,
    avg_rate: float,
) -> tuple[Path, Path, Path, dict[str, Any]]:
    """Ecrit les outputs du batch."""
    bib_root = ensure_dir(bibliotheque_root())
    reports_dir = ensure_dir(reports_root())
    archives_dir = ensure_dir(archives_root())

    tag = _timestamp_tag()
    bibliotheque_path = _unique_path(bib_root / f"bibliotheque_{tag}.csv")
    to_be_downloaded_path = _unique_path(bib_root / f"to_be_downloaded_{tag}.csv")
    report_path = _unique_path(reports_dir / f"run_report_{tag}.txt")

    df.to_csv(bibliotheque_path, index=False)
    failed_df = df[df["status"] != "downloaded"]
    failed_df.to_csv(to_be_downloaded_path, index=False)
    _archive_old_downloads(bib_root, archives_dir, to_be_downloaded_path)
    catalog_result = sync_catalog(bibliotheque_path)

    total = len(df)
    downloaded = int((df["status"] == "downloaded").sum())
    failed = total - downloaded
    rate = (downloaded / total) if total else 0.0
    reason_counts = Counter(failed_df["reason_code"])
    oa_true: int | None = None
    oa_false: int | None = None
    if "is_oa" in df.columns:
        oa_flags = [_parse_bool(value) for value in df["is_oa"]]
        oa_true = sum(flag is True for flag in oa_flags)
        oa_false = sum(flag is False for flag in oa_flags)
    http_counts = Counter()
    if "last_http_status" in df.columns:
        for value in df["last_http_status"]:
            text = str(value).strip()
            if text and text.lower() != "nan":
                http_counts[text] += 1

    report_lines = [
        report_title,
        f"Total: {total}",
        f"Telecharges: {downloaded}",
        f"Echecs: {failed}",
        f"Taux de recuperation: {rate:.1%}",
        f"Duree: {duration_sec:.1f}s",
        f"Vitesse moyenne: {avg_rate:.2f} items/s",
    ]
    if downloaded and duration_sec > 0:
        pdf_rate = downloaded / (duration_sec / 60)
        report_lines.append(f"Vitesse moyenne PDF: {pdf_rate:.2f} pdf/min")
    if oa_true is not None and oa_false is not None:
        report_lines.append(f"OA True: {oa_true}")
        report_lines.append(f"OA False: {oa_false}")

    report_lines.append("Raisons d echec:")
    if reason_counts:
        for reason, count in reason_counts.most_common():
            report_lines.append(f"- {reason}: {count}")
    else:
        report_lines.append("- aucune")

    report_lines.append("HTTP status:")
    if http_counts:
        for status, count in http_counts.most_common():
            report_lines.append(f"- {status}: {count}")
    else:
        report_lines.append("- aucun")

    report_lines.append("DOI en echec:")
    if failed_df.empty:
        report_lines.append("- aucun")
    else:
        for index, row in failed_df.iterrows():
            value = row[doi_column] if doi_column in failed_df.columns else ""
            report_lines.append(f"- {_format_doi(value, index)} ({row['reason_code']})")

    report_lines.append("Fichiers:")
    report_lines.append(f"- Bibliotheque: {bibliotheque_path}")
    report_lines.append(f"- A telecharger: {to_be_downloaded_path}")
    report_lines.append(f"- Rapport: {report_path}")
    report_lines.append(f"- Catalog diff: {catalog_result['diff_path']}")

    pdf_paths = [path for path in df["pdf_path"] if path]
    if pdf_paths:
        report_lines.append("PDFs:")
        for path in pdf_paths:
            report_lines.append(f"- {path}")

    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return bibliotheque_path, to_be_downloaded_path, report_path, catalog_result


def _latest_to_be_downloaded(bib_root: Path) -> Path | None:
    """Trouve le dernier to_be_downloaded."""
    candidates = list(bib_root.glob("to_be_downloaded_*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def attempt_unpaywall_download(
    doi: str,
    collection: Path,
    min_pdf_kb: int = DEFAULT_MIN_PDF_KB,
    log: Callable[[str], None] | None = None,
    on_try: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Tente un download via Unpaywall."""
    def emit(message: str) -> None:
        if log is not None:
            log(message)

    def emit_try(method: str) -> None:
        if on_try is not None:
            on_try(method)

    result = resolve_pdf_urls_from_unpaywall(doi)
    is_oa = result.get("is_oa")
    oa_status = result.get("oa_status")
    url_for_pdf = result.get("url_for_pdf")
    candidates = result.get("candidates", [])
    candidates_total = len(candidates)
    tried_count = 0
    last_reason: str | None = None
    last_final_url: str | None = None
    last_http_status: int | None = None
    tried_methods: list[str] = []
    last_method: str | None = None

    def record_method(method: str) -> None:
        nonlocal last_method
        last_method = method
        if method not in tried_methods:
            tried_methods.append(method)
        emit_try(method)

    if result.get("status") == "error":
        return {
            "doi": doi,
            "status": "failed",
            "reason_code": "ERROR",
            "pdf_path": None,
            "final_url": None,
            "candidates_total": candidates_total,
            "tried_count": tried_count,
            "error": result.get("error") or "Unpaywall error",
            "pdf_bytes_len": None,
            "is_oa": is_oa,
            "oa_status": oa_status,
            "url_for_pdf": url_for_pdf,
            "last_http_status": last_http_status,
            "tried_methods": "",
            "last_method": last_method,
        }

    if not candidates:
        return {
            "doi": doi,
            "status": "failed",
            "reason_code": "NO_PDF_FOUND",
            "pdf_path": None,
            "final_url": None,
            "candidates_total": candidates_total,
            "tried_count": tried_count,
            "error": None,
            "pdf_bytes_len": None,
            "is_oa": is_oa,
            "oa_status": oa_status,
            "url_for_pdf": url_for_pdf,
            "last_http_status": last_http_status,
            "tried_methods": "",
            "last_method": last_method,
        }

    for candidate in candidates:
        url = candidate.get("url")
        kind = candidate.get("kind", "unknown")
        if not url:
            continue
        if kind == "pdf":
            record_method("unpaywall_url_for_pdf")
        elif kind == "landing":
            record_method("unpaywall_landing")
        else:
            record_method(f"unpaywall_{kind}")
        emit(f"Essai: {kind} {url}")
        ok, status_code, content_type, final_url, content, error_code = fetch_url(url)
        tried_count += 1
        last_final_url = final_url or url
        if status_code:
            last_http_status = status_code
        if not ok:
            last_reason = _map_fetch_failure(status_code, error_code)
            emit(f"Echec fetch ({status_code})")
            continue

        ok_pdf, code = validate_pdf_bytes(content, min_size_kb=min_pdf_kb)
        if ok_pdf:
            pdf_path = store_pdf_bytes(collection, doi, content)
            emit(f"PDF valide: {pdf_path}")
            return {
                "doi": doi,
                "status": "downloaded",
                "reason_code": "OK",
                "pdf_path": pdf_path,
                "final_url": last_final_url,
                "candidates_total": candidates_total,
                "tried_count": tried_count,
                "error": None,
                "pdf_bytes_len": len(content),
                "is_oa": is_oa,
                "oa_status": oa_status,
                "url_for_pdf": url_for_pdf,
                "last_http_status": last_http_status,
                "tried_methods": "|".join(tried_methods),
                "last_method": last_method,
            }

        if kind == "landing" and _is_html_content(content_type, content):
            html = content.decode("utf-8", errors="ignore")
            pdf_urls = extract_pdf_urls_from_html(html, last_final_url)
            if pdf_urls:
                emit(f"Landing HTML: {len(pdf_urls)} liens PDF")
            elif last_reason is None:
                last_reason = "NO_PDF_FOUND"
            for pdf_url in pdf_urls:
                record_method("landing_pdf_link")
                ok_pdf_url, status_code, _, final_pdf_url, pdf_bytes, error_code = (
                    fetch_url(pdf_url)
                )
                tried_count += 1
                last_final_url = final_pdf_url or pdf_url
                if status_code:
                    last_http_status = status_code
                if not ok_pdf_url:
                    last_reason = _map_fetch_failure(status_code, error_code)
                    emit(f"Echec fetch ({status_code}): {final_pdf_url}")
                    continue
                ok_pdf, code = validate_pdf_bytes(
                    pdf_bytes, min_size_kb=min_pdf_kb
                )
                if ok_pdf:
                    pdf_path = store_pdf_bytes(collection, doi, pdf_bytes)
                    emit(f"PDF valide: {pdf_path}")
                    return {
                        "doi": doi,
                        "status": "downloaded",
                        "reason_code": "OK",
                        "pdf_path": pdf_path,
                        "final_url": last_final_url,
                        "candidates_total": candidates_total,
                        "tried_count": tried_count,
                        "error": None,
                        "pdf_bytes_len": len(pdf_bytes),
                        "is_oa": is_oa,
                        "oa_status": oa_status,
                        "url_for_pdf": url_for_pdf,
                        "last_http_status": last_http_status,
                        "tried_methods": "|".join(tried_methods),
                        "last_method": last_method,
                    }
                last_reason = _map_validation_code(code)
                emit(f"PDF invalide: {code}")
            continue

        last_reason = _map_validation_code(code)
        emit(f"PDF invalide: {code}")

    if last_reason is None:
        last_reason = "NO_PDF_FOUND"

    return {
        "doi": doi,
        "status": "failed",
        "reason_code": last_reason,
        "pdf_path": None,
        "final_url": last_final_url,
        "candidates_total": candidates_total,
        "tried_count": tried_count,
        "error": None,
        "pdf_bytes_len": None,
        "is_oa": is_oa,
        "oa_status": oa_status,
        "url_for_pdf": url_for_pdf,
        "last_http_status": last_http_status,
        "tried_methods": "|".join(tried_methods),
        "last_method": last_method,
    }


def _demo_dataframe() -> pd.DataFrame:
    """Cree un DataFrame de demo."""
    rows = [
        {
            "type": "article",
            "title": "Demo Article 1",
            "doi": "10.1371/journal.pone.0259580",
            "authors": "Alice Doe; Bob Roe",
            "year": "2021",
            "keywords": "demo; oa",
        },
        {
            "type": "article",
            "title": "Demo Article 2",
            "doi": "10.7717/peerj.4375",
            "authors": "Cara Poe",
            "year": "2018",
            "keywords": "demo; peerj",
        },
        {
            "type": "article",
            "title": "Demo Article 3",
            "doi": "10.1038/nphys1170",
            "authors": "Dan Moe",
            "year": "2008",
            "keywords": "demo; physics",
        },
    ]
    columns = ["type", "title", "doi", "authors", "year", "keywords"]
    return pd.DataFrame(rows, columns=columns)


def run_unpaywall_demo_batch(verbose_progress: bool = False) -> int:
    """Execute un batch Unpaywall demo."""
    df = _demo_dataframe()
    ensure_dir(library_root())
    collections_dir = ensure_dir(collections_root())
    collection = choose_collection(collections_dir)
    if collection is None:
        print("Aucune collection choisie.")
        return 0

    df = df.copy()
    df["status"] = ""
    df["reason_code"] = ""
    df["pdf_path"] = ""
    df["final_url"] = ""
    df["is_oa"] = ""
    df["oa_status"] = ""
    df["url_for_pdf"] = ""
    df["last_http_status"] = ""
    df["tried_methods"] = ""
    df["collection"] = _collection_label(collection)
    _ensure_str_columns(
        df,
        [
            "status",
            "reason_code",
            "pdf_path",
            "final_url",
            "is_oa",
            "oa_status",
            "url_for_pdf",
            "last_http_status",
            "tried_methods",
        ],
    )

    total = len(df)
    processed = 0
    ok_count = 0
    fail_count = 0
    start_time = time.monotonic()
    durations: list[float] = []
    cancelled = False
    progress_len = 0

    try:
        for index, row in df.iterrows():
            doi = str(row["doi"]).strip()
            item_start = time.monotonic()
            result = attempt_unpaywall_download(
                doi, collection, min_pdf_kb=DEFAULT_MIN_PDF_KB
            )
            status = result["status"]
            reason_code = result["reason_code"]
            bytes_len = result.get("pdf_bytes_len")
            method = result.get("last_method") or ""
            df.at[index, "status"] = status
            df.at[index, "reason_code"] = reason_code
            df.at[index, "pdf_path"] = str(result["pdf_path"] or "")
            df.at[index, "final_url"] = result["final_url"] or ""
            df.at[index, "is_oa"] = (
                "" if result.get("is_oa") is None else str(result.get("is_oa"))
            )
            df.at[index, "oa_status"] = str(result.get("oa_status") or "")
            df.at[index, "url_for_pdf"] = str(result.get("url_for_pdf") or "")
            df.at[index, "last_http_status"] = str(
                result.get("last_http_status") or ""
            )
            df.at[index, "tried_methods"] = str(result.get("tried_methods") or "")

            processed += 1
            if status == "downloaded":
                ok_count += 1
            else:
                fail_count += 1

            item_elapsed = time.monotonic() - item_start
            durations.append(item_elapsed)
            if len(durations) > PROGRESS_WINDOW:
                durations.pop(0)

            if verbose_progress:
                print(
                    _verbose_item_line(
                        processed,
                        total,
                        doi,
                        status,
                        reason_code,
                        method,
                        item_elapsed,
                        bytes_len,
                        ok_count,
                        fail_count,
                        durations,
                    ),
                    flush=True,
                )
            else:
                progress_len = _print_compact_progress(
                    _progress_line(processed, total, ok_count, fail_count, durations),
                    progress_len,
                )
    except KeyboardInterrupt:
        cancelled = True
        if not verbose_progress and processed:
            print("", flush=True)
        print("Annulé", flush=True)

    if cancelled:
        _mark_unprocessed_as_error(df)
    elif not verbose_progress and processed:
        print("", flush=True)

    duration_sec = time.monotonic() - start_time
    avg_rate = (processed / duration_sec) if duration_sec > 0 else 0.0

    (
        bibliotheque_path,
        to_be_downloaded_path,
        report_path,
        catalog_result,
    ) = _write_batch_outputs(
        df, "doi", "Rapport Unpaywall batch", duration_sec, avg_rate
    )

    print("")
    print(f"Bibliotheque: {bibliotheque_path}")
    print(f"A telecharger: {to_be_downloaded_path}")
    print(f"Rapport: {report_path}")
    print(f"Catalog diff: {catalog_result['diff_path']}")
    return 0


def run_unpaywall_csv_batch(
    csv_path: Path | str,
    collection: Path,
    limit: int | None = None,
    progress_every: int = DEFAULT_PROGRESS_EVERY,
    verbose_progress: bool = False,
) -> int:
    """Execute un batch Unpaywall CSV."""
    csv_path = Path(csv_path).expanduser()
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        print(f"Erreur lecture CSV: {exc}")
        return 2

    if df.empty:
        print("CSV vide.")

    ensure_dir(library_root())

    df = df.copy()
    doi_column = _find_column(df.columns, ["doi_clean", "doi", "DOI"])
    if doi_column is None:
        df["doi"] = ""
        doi_column = "doi"
    df[doi_column] = df[doi_column].apply(_normalize_doi)
    df["doi"] = df[doi_column]

    type_column = _find_column(df.columns, ["type"])
    if type_column is None:
        df["type"] = "article"
    elif type_column != "type":
        if "type" not in df.columns:
            df["type"] = df[type_column]
    df["type"] = df["type"].apply(_normalize_type)

    for name in ["title", "authors", "year", "keywords"]:
        source = _find_column(df.columns, [name])
        if source is None:
            df[name] = ""
        elif name not in df.columns:
            df[name] = df[source]

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
    ]:
        df[name] = ""
    _ensure_str_columns(
        df,
        [
            "status",
            "reason_code",
            "pdf_path",
            "final_url",
            "is_oa",
            "oa_status",
            "url_for_pdf",
            "last_http_status",
            "tried_methods",
        ],
    )

    df["collection"] = _collection_label(collection)

    if limit is not None and limit > 0:
        df = df.head(limit)

    total = len(df)
    if total:
        print(f"Lignes a traiter: {total}")

    processed = 0
    ok_count = 0
    fail_count = 0
    start_time = time.monotonic()
    durations: list[float] = []
    cancelled = False
    progress_len = 0

    try:
        for offset, (index, row) in enumerate(df.iterrows(), start=1):
            doi = str(row[doi_column]).strip()
            item_type = str(row["type"]).strip().lower()
            item_start = time.monotonic()

            status = ""
            reason_code = ""
            pdf_path = ""
            final_url = ""
            bytes_len: int | None = None
            method = ""
            is_oa = ""
            oa_status = ""
            url_for_pdf = ""
            last_http_status = ""
            tried_methods = ""

            if item_type and item_type != "article":
                status = "failed"
                reason_code = "ERROR"
            elif not doi:
                status = "failed"
                reason_code = "MISSING_DOI"
            else:
                result = attempt_unpaywall_download(
                    doi, collection, min_pdf_kb=DEFAULT_MIN_PDF_KB
                )
                status = result["status"]
                reason_code = result["reason_code"]
                pdf_path = str(result["pdf_path"] or "")
                final_url = result["final_url"] or ""
                bytes_len = result.get("pdf_bytes_len")
                method = result.get("last_method") or ""
                is_oa = "" if result.get("is_oa") is None else str(result.get("is_oa"))
                oa_status = str(result.get("oa_status") or "")
                url_for_pdf = str(result.get("url_for_pdf") or "")
                last_http_status = str(result.get("last_http_status") or "")
                tried_methods = str(result.get("tried_methods") or "")

            df.at[index, "status"] = status
            df.at[index, "reason_code"] = reason_code
            df.at[index, "pdf_path"] = pdf_path
            df.at[index, "final_url"] = final_url
            df.at[index, "is_oa"] = is_oa
            df.at[index, "oa_status"] = oa_status
            df.at[index, "url_for_pdf"] = url_for_pdf
            df.at[index, "last_http_status"] = last_http_status
            df.at[index, "tried_methods"] = tried_methods

            processed = offset
            if status == "downloaded":
                ok_count += 1
            else:
                fail_count += 1

            item_elapsed = time.monotonic() - item_start
            durations.append(item_elapsed)
            if len(durations) > PROGRESS_WINDOW:
                durations.pop(0)

            if verbose_progress:
                print(
                    _verbose_item_line(
                        offset,
                        total,
                        doi or "<manquant>",
                        status,
                        reason_code,
                        method,
                        item_elapsed,
                        bytes_len,
                        ok_count,
                        fail_count,
                        durations,
                    ),
                    flush=True,
                )
            else:
                progress_len = _print_compact_progress(
                    _progress_line(offset, total, ok_count, fail_count, durations),
                    progress_len,
                )
    except KeyboardInterrupt:
        cancelled = True
        if not verbose_progress and processed:
            print("", flush=True)
        print("Annulé", flush=True)

    if cancelled:
        _mark_unprocessed_as_error(df)
    elif not verbose_progress and processed:
        print("", flush=True)

    duration_sec = time.monotonic() - start_time
    avg_rate = (processed / duration_sec) if duration_sec > 0 else 0.0

    (
        bibliotheque_path,
        to_be_downloaded_path,
        report_path,
        catalog_result,
    ) = _write_batch_outputs(
        df, doi_column, "Rapport Unpaywall CSV", duration_sec, avg_rate
    )

    print("")
    print(f"Bibliotheque: {bibliotheque_path}")
    print(f"A telecharger: {to_be_downloaded_path}")
    print(f"Rapport: {report_path}")
    print(f"Catalog diff: {catalog_result['diff_path']}")
    return 0


def run_unpaywall_queue(
    limit: int | None = None,
    progress_every: int = DEFAULT_PROGRESS_EVERY,
    verbose_progress: bool = False,
) -> int:
    """Execute un batch Unpaywall depuis la queue."""
    ensure_dir(library_root())
    bib_root = ensure_dir(bibliotheque_root())
    queue_path = _latest_to_be_downloaded(bib_root)
    if queue_path is None:
        print("Aucun fichier to_be_downloaded.")
        return 0

    try:
        df = pd.read_csv(queue_path)
    except Exception as exc:
        print(f"Erreur lecture queue: {exc}")
        return 2

    df = df.copy()
    doi_column = _find_column(df.columns, ["doi_clean", "doi", "DOI"])
    if doi_column is None:
        df["doi"] = ""
        doi_column = "doi"
    df[doi_column] = df[doi_column].apply(_normalize_doi)
    df["doi"] = df[doi_column]

    for name in ["title", "authors", "year", "keywords", "type"]:
        if name not in df.columns:
            df[name] = ""

    for name in [
        "status",
        "reason_code",
        "pdf_path",
        "final_url",
        "collection",
        "is_oa",
        "oa_status",
        "url_for_pdf",
        "last_http_status",
        "tried_methods",
    ]:
        if name not in df.columns:
            df[name] = ""
    _ensure_str_columns(
        df,
        [
            "status",
            "reason_code",
            "pdf_path",
            "final_url",
            "collection",
            "is_oa",
            "oa_status",
            "url_for_pdf",
            "last_http_status",
            "tried_methods",
        ],
    )

    status_series = df["status"].astype(str).str.strip().str.lower()
    failed_mask = status_series == "failed"
    if not failed_mask.any():
        failed_mask = status_series == ""
    to_process = df.index[failed_mask].tolist()
    if limit is not None and limit > 0:
        to_process = to_process[:limit]

    total = len(to_process)
    if total == 0:
        print("Aucun item a traiter.")
        return 0

    default_collection: Path | None = None
    collection_values = df.loc[to_process, "collection"].astype(str).str.strip()
    needs_default = collection_values.eq("") | collection_values.str.lower().eq("nan")
    if needs_default.any():
        try:
            default_collection = choose_collection(collections_root())
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if default_collection is None:
            print("Annulé")
            return 0

    processed = 0
    ok_count = 0
    fail_count = 0
    start_time = time.monotonic()
    durations: list[float] = []
    cancelled = False
    progress_len = 0
    for index in to_process:
        try:
            item_start = time.monotonic()
            doi = str(df.at[index, doi_column]).strip()
            status = ""
            reason_code = ""
            pdf_path = ""
            final_url = ""
            bytes_len: int | None = None
            method = ""
            is_oa = ""
            oa_status = ""
            url_for_pdf = ""
            last_http_status = ""
            tried_methods = ""
            if not doi:
                status = "failed"
                reason_code = "MISSING_DOI"
            else:
                collection_value = df.at[index, "collection"]
                collection_path = _resolve_collection_path(
                    collection_value, default_collection
                )
                if collection_path is None:
                    status = "failed"
                    reason_code = "ERROR"
                else:
                    collection_path = ensure_dir(collection_path)
                    df.at[index, "collection"] = _collection_label(collection_path)
                    result = attempt_unpaywall_download(
                        doi, collection_path, min_pdf_kb=DEFAULT_MIN_PDF_KB
                    )
                    status = result["status"]
                    reason_code = result["reason_code"]
                    pdf_path = str(result["pdf_path"] or "")
                    final_url = result["final_url"] or ""
                    bytes_len = result.get("pdf_bytes_len")
                    method = result.get("last_method") or ""
                    is_oa = (
                        "" if result.get("is_oa") is None else str(result.get("is_oa"))
                    )
                    oa_status = str(result.get("oa_status") or "")
                    url_for_pdf = str(result.get("url_for_pdf") or "")
                    last_http_status = str(result.get("last_http_status") or "")
                    tried_methods = str(result.get("tried_methods") or "")

            df.at[index, "status"] = status
            df.at[index, "reason_code"] = reason_code
            df.at[index, "pdf_path"] = pdf_path
            df.at[index, "final_url"] = final_url
            df.at[index, "is_oa"] = is_oa
            df.at[index, "oa_status"] = oa_status
            df.at[index, "url_for_pdf"] = url_for_pdf
            df.at[index, "last_http_status"] = last_http_status
            df.at[index, "tried_methods"] = tried_methods

            processed += 1
            if status == "downloaded":
                ok_count += 1
            else:
                fail_count += 1
            item_elapsed = time.monotonic() - item_start
            durations.append(item_elapsed)
            if len(durations) > PROGRESS_WINDOW:
                durations.pop(0)
            if verbose_progress:
                print(
                    _verbose_item_line(
                        processed,
                        total,
                        doi or "<manquant>",
                        status,
                        reason_code,
                        method,
                        item_elapsed,
                        bytes_len,
                        ok_count,
                        fail_count,
                        durations,
                    ),
                    flush=True,
                )
        except KeyboardInterrupt:
            cancelled = True
            if not verbose_progress and processed:
                print("", flush=True)
            print("Annulé", flush=True)
            break
        if not verbose_progress:
            progress_len = _print_compact_progress(
                _progress_line(processed, total, ok_count, fail_count, durations),
                progress_len,
            )

    if cancelled:
        for index in to_process[processed:]:
            if str(df.at[index, "status"]).strip() == "":
                df.at[index, "status"] = "failed"
            if str(df.at[index, "reason_code"]).strip() == "":
                df.at[index, "reason_code"] = "ERROR"
    elif not verbose_progress and processed:
        print("", flush=True)

    duration_sec = time.monotonic() - start_time
    avg_rate = (processed / duration_sec) if duration_sec > 0 else 0.0

    (
        bibliotheque_path,
        to_be_downloaded_path,
        report_path,
        catalog_result,
    ) = _write_batch_outputs(
        df, doi_column, "Rapport Unpaywall queue", duration_sec, avg_rate
    )

    print("")
    print(f"Bibliotheque: {bibliotheque_path}")
    print(f"A telecharger: {to_be_downloaded_path}")
    print(f"Rapport: {report_path}")
    print(f"Catalog diff: {catalog_result['diff_path']}")
    return 0
