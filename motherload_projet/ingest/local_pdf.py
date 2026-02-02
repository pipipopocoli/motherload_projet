"""Ingestion locale de PDFs."""

from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from motherload_projet.config import get_manual_import_subdir
from motherload_projet.library.master_catalog import (
    load_master_catalog,
    upsert_manual_pdf_entry,
    upsert_scan_pdf_entry,
)
from motherload_projet.library.paths import (
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
    reports_root,
)


def _timestamp_tag() -> str:
    """Genere un horodatage."""
    return datetime.now().strftime("%Y%m%d_%H%M")


def _unique_path(base: Path) -> Path:
    """Retourne un chemin unique sans ecraser."""
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = base.with_name(f"{base.stem}_{counter:02d}{base.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _resolve_collection_label(collection: str | Path) -> str:
    """Retourne un label de collection relatif."""
    base = collections_root()
    candidate = Path(collection)
    if candidate.is_absolute():
        try:
            relative = candidate.relative_to(base)
        except ValueError:
            relative = Path(candidate.name)
    else:
        relative = candidate
    return str(relative)


def _infer_collection_from_pdf_path(path: Path) -> str:
    """Deduit la collection depuis un PDF."""
    pdf_root = library_root() / "pdfs"
    try:
        rel = path.resolve().relative_to(pdf_root.resolve())
    except (OSError, ValueError):
        return ""
    parts = rel.parts
    if len(parts) >= 3:
        collection_parts = parts[:-2]
    elif len(parts) == 2:
        collection_parts = (parts[0],)
    else:
        collection_parts = ()
    if not collection_parts:
        return ""
    return str(Path(*collection_parts))

def _validate_pdf(path: Path) -> tuple[bool, str]:
    """Valide un PDF par extension et header."""
    if not path.exists() or not path.is_file():
        return False, "MISSING_FILE"
    if path.suffix.lower() != ".pdf":
        return False, "NOT_PDF_EXT"
    try:
        with path.open("rb") as handle:
            head = handle.read(5)
    except OSError:
        return False, "READ_ERROR"
    if not head.startswith(b"%PDF-"):
        return False, "NOT_PDF_HEADER"
    return True, "OK"


def compute_file_hash(path: Path) -> str:
    """Calcule un hash sha256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def ensure_unique_target_path(target_dir: Path, filename: str) -> Path:
    """Assure un nom de fichier unique."""
    candidate = target_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        name = f"{stem}_{counter:02d}{suffix}"
        candidate = target_dir / name
        if not candidate.exists():
            return candidate
        counter += 1


def _manual_subdir(value: str | None) -> str:
    """Retourne le sous-dossier manuel."""
    if value is None or not value.strip():
        return get_manual_import_subdir()
    return value.strip()


def _is_valid_isbn10(value: str) -> bool:
    """Valide un ISBN-10."""
    if len(value) != 10:
        return False
    total = 0
    for index, char in enumerate(value, start=1):
        if char == "X":
            digit = 10
        elif char.isdigit():
            digit = int(char)
        else:
            return False
        total += (11 - index) * digit
    return total % 11 == 0


def _is_valid_isbn13(value: str) -> bool:
    """Valide un ISBN-13."""
    if len(value) != 13 or not value.isdigit():
        return False
    total = 0
    for index, char in enumerate(value[:-1]):
        digit = int(char)
        total += digit * (1 if index % 2 == 0 else 3)
    check = (10 - (total % 10)) % 10
    return check == int(value[-1])


def _extract_isbn_from_text(text: str) -> str | None:
    """Extrait un ISBN depuis un texte."""
    if not text:
        return None
    candidates = re.findall(r"[0-9Xx][0-9Xx -]{8,20}[0-9Xx]", text)
    for raw in candidates:
        cleaned = re.sub(r"[^0-9Xx]", "", raw).upper()
        if len(cleaned) == 10 and _is_valid_isbn10(cleaned):
            return cleaned
        if len(cleaned) == 13 and _is_valid_isbn13(cleaned):
            return cleaned
    for raw in candidates:
        cleaned = re.sub(r"[^0-9Xx]", "", raw).upper()
        if len(cleaned) in {10, 13}:
            return cleaned
    return None


def _extract_isbn_from_pdf(path: Path) -> str | None:
    """Extrait un ISBN depuis un PDF."""
    try:
        reader = PdfReader(str(path))
    except Exception:
        return None
    chunks: list[str] = []
    meta = getattr(reader, "metadata", None)
    if meta:
        for value in meta.values():
            if isinstance(value, str):
                chunks.append(value)
    for page in reader.pages[:2]:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            chunks.append(text)
    combined = " ".join(chunks)
    return _extract_isbn_from_text(combined)


def _extract_pdf_metadata(path: Path) -> dict[str, str]:
    """Extrait des metadonnees du PDF."""
    data: dict[str, str] = {}
    try:
        reader = PdfReader(str(path))
    except Exception:
        return data

    meta = getattr(reader, "metadata", None)
    if meta:
        title = meta.get("/Title") if isinstance(meta, dict) else None
        author = meta.get("/Author") if isinstance(meta, dict) else None
        keywords = meta.get("/Keywords") if isinstance(meta, dict) else None
        created = meta.get("/CreationDate") if isinstance(meta, dict) else None
        if isinstance(title, str) and title.strip():
            data["title"] = title.strip()
        if isinstance(author, str) and author.strip():
            data["authors"] = author.strip()
        if isinstance(keywords, str) and keywords.strip():
            data["keywords"] = keywords.strip()
        if isinstance(created, str):
            match = re.search(r"(19|20)\\d{2}", created)
            if match:
                data["year"] = match.group(0)

    return data


def _guess_doc_type(path: Path) -> tuple[str, str | None]:
    """Devine le type de document."""
    name = path.stem
    lower_name = name.lower()
    isbn = _extract_isbn_from_text(name)
    if isbn is None:
        isbn = _extract_isbn_from_pdf(path)
    if isbn:
        return "book", isbn

    path_text = " ".join(path.parts).lower()
    if any(word in lower_name for word in ("book", "livre", "ouvrage")):
        return "book", None
    if any(word in path_text for word in ("book", "livre", "ouvrage")):
        return "book", None

    return "unknown", None


def ingest_pdf(pdf_path: Path, collection: str, subdir: str | None) -> dict[str, Any]:
    """Ingere un PDF local."""
    path = Path(pdf_path).expanduser()
    ok, reason = _validate_pdf(path)
    title_guess = path.stem
    collection_label = _resolve_collection_label(collection)
    if not ok:
        return {
            "status": "error",
            "reason_code": "ERROR",
            "error": reason,
            "pdf_path": None,
            "file_hash": "",
            "title_guess": title_guess,
            "collection": collection_label,
            "master_action": "error",
        }

    file_hash = compute_file_hash(path)
    master_path = ensure_dir(bibliotheque_root()) / "master_catalog.csv"
    master_df = load_master_catalog(master_path)
    if "file_hash" in master_df.columns:
        hashes = master_df["file_hash"].fillna("").astype(str).str.strip()
        if file_hash and file_hash in set(hashes):
            return {
                "status": "skipped",
                "reason_code": "DUPLICATE_HASH",
                "error": None,
                "pdf_path": None,
                "file_hash": file_hash,
                "title_guess": title_guess,
                "collection": collection_label,
                "master_action": "existing",
            }

    subdir_value = _manual_subdir(subdir)
    pdf_root = ensure_dir(library_root() / "pdfs")
    target_dir = ensure_dir(pdf_root / Path(collection_label) / subdir_value)
    target_path = ensure_unique_target_path(target_dir, path.name)
    try:
        shutil.move(str(path), str(target_path))
    except OSError as exc:
        return {
            "status": "error",
            "reason_code": "ERROR",
            "error": f"MOVE_ERROR: {exc}",
            "pdf_path": None,
            "file_hash": file_hash,
            "title_guess": title_guess,
            "collection": collection_label,
            "master_action": "error",
        }

    doc_type, isbn = _guess_doc_type(target_path)
    meta = _extract_pdf_metadata(target_path)
    added_at = datetime.now().isoformat(timespec="seconds")
    entry = {
        "file_hash": file_hash,
        "source": "manual",
        "added_at": added_at,
        "collection": collection_label,
        "pdf_path": str(target_path),
        "type": doc_type,
        "title": meta.get("title") or title_guess,
    }
    if isbn:
        entry["isbn"] = isbn
    if meta.get("authors"):
        entry["authors"] = meta["authors"]
    if meta.get("keywords"):
        entry["keywords"] = meta["keywords"]
    if meta.get("year"):
        entry["year"] = meta["year"]
    run_tag = _timestamp_tag()
    master_df, diff = upsert_manual_pdf_entry(master_df, entry, run_tag)
    master_df.to_csv(master_path, index=False)

    return {
        "status": "ok",
        "reason_code": "OK",
        "error": None,
        "pdf_path": str(target_path),
        "file_hash": file_hash,
        "title_guess": target_path.stem,
        "collection": collection_label,
        "master_action": diff.get("action", "created"),
    }


def write_manual_ingest_report(results: list[dict[str, Any]]) -> Path:
    """Ecrit un rapport d ingestion manuelle."""
    reports_dir = ensure_dir(reports_root())
    report_path = _unique_path(
        reports_dir / f"manual_ingest_{_timestamp_tag()}.txt"
    )
    total = len(results)
    ok_count = sum(1 for item in results if item.get("status") == "ok")
    duplicate_count = sum(
        1 for item in results if item.get("reason_code") == "DUPLICATE_HASH"
    )
    error_count = sum(1 for item in results if item.get("status") == "error")
    new_items = sum(1 for item in results if item.get("master_action") == "created")
    existing_items = sum(
        1
        for item in results
        if item.get("master_action") in {"updated", "existing"}
    )

    lines = [
        "Rapport manual ingest",
        f"Total fichiers: {total}",
        f"OK: {ok_count}",
        f"DUPLICATE: {duplicate_count}",
        f"ERROR: {error_count}",
        "Chemins importes:",
    ]
    for item in results:
        if item.get("status") == "ok" and item.get("pdf_path"):
            lines.append(f"- {item['pdf_path']}")

    lines.extend(
        [
            "Diff master_catalog:",
            f"Nouvelles entrees: {new_items}",
            f"Deja existantes: {existing_items}",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def scan_library_pdfs(pdf_root: Path | None = None) -> dict[str, Any]:
    """Analyse les PDFs deja dans la librairie."""
    pdf_root = Path(pdf_root) if pdf_root else (library_root() / "pdfs")
    if not pdf_root.exists():
        return {"total": 0, "updated": 0, "created": 0, "errors": 0}

    master_path = ensure_dir(bibliotheque_root()) / "master_catalog.csv"
    master_df = load_master_catalog(master_path)
    run_tag = _timestamp_tag()
    report_lines: list[str] = []

    total = 0
    updated = 0
    created = 0
    errors = 0

    for pdf_path in pdf_root.rglob("*.pdf"):
        if not pdf_path.is_file():
            continue
        total += 1
        ok, reason = _validate_pdf(pdf_path)
        if not ok:
            errors += 1
            report_lines.append(f"- {pdf_path} | {reason}")
            continue

        try:
            file_hash = compute_file_hash(pdf_path)
            doc_type, isbn = _guess_doc_type(pdf_path)
            meta = _extract_pdf_metadata(pdf_path)
            collection_label = _infer_collection_from_pdf_path(pdf_path)
            entry = {
                "file_hash": file_hash,
                "pdf_path": str(pdf_path),
                "collection": collection_label,
                "type": doc_type,
                "title": meta.get("title") or pdf_path.stem,
                "source": "library",
                "added_at": datetime.now().isoformat(timespec="seconds"),
            }
            if isbn:
                entry["isbn"] = isbn
            if meta.get("authors"):
                entry["authors"] = meta["authors"]
            if meta.get("keywords"):
                entry["keywords"] = meta["keywords"]
            if meta.get("year"):
                entry["year"] = meta["year"]

            master_df, diff = upsert_scan_pdf_entry(master_df, entry, run_tag)
            action = diff.get("action")
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
        except Exception as exc:
            errors += 1
            report_lines.append(f"- {pdf_path} | EXC: {exc}")

    master_df.to_csv(master_path, index=False)
    report_path = None
    if report_lines:
        reports_dir = ensure_dir(reports_root())
        report_path = _unique_path(
            reports_dir / f"library_scan_report_{_timestamp_tag()}.txt"
        )
        summary = [
            "Library scan report",
            f"Total PDFs: {total}",
            f"Created: {created}",
            f"Updated: {updated}",
            f"Errors: {errors}",
            "Errors detail:",
        ]
        report_path.write_text(
            "\n".join(summary + report_lines) + "\n", encoding="utf-8"
        )

    return {
        "total": total,
        "updated": updated,
        "created": created,
        "errors": errors,
        "master_path": str(master_path),
        "report_path": str(report_path) if report_path else None,
    }
