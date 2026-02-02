"""Pipeline de scan PDF pour catalogues."""

from __future__ import annotations

import json
import os
import re
import time
import hashlib
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
from pypdf import PdfReader

from motherload_projet.catalogs.schema import ScanConfig, ScanRunSummary
from motherload_projet.catalogs.scoring import (
    CompletenessConfig,
    fingerprint,
    first_author_last,
    is_complete,
    primary_id,
)
from motherload_projet.catalogs.exporters import export_bibtex, export_catalogs
from motherload_projet.catalogs.reports import write_reports
from motherload_projet.config import get_crossref_email, get_unpaywall_email
from motherload_projet.library.master_catalog import load_master_catalog
from motherload_projet.library.paths import bibliotheque_root, ensure_dir, library_root, reports_root

DEFAULT_SCAN_COLUMNS = [
    "primary_id",
    "fingerprint",
    "version",
    "replaced_by",
    "journal",
    "venue",
    "volume",
    "issue",
    "pages",
    "url",
]


def _timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for name in columns:
        if name not in df.columns:
            df[name] = ""
    return df


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_isbn_from_text(text: str) -> str | None:
    if not text:
        return None
    candidates = re.findall(r"[0-9Xx][0-9Xx -]{8,20}[0-9Xx]", text)
    for raw in candidates:
        cleaned = re.sub(r"[^0-9Xx]", "", raw).upper()
        if len(cleaned) in {10, 13}:
            return cleaned
    return None


def _clean_doi(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", cleaned, flags=re.I)
    cleaned = re.sub(r"^doi:\s*", "", cleaned, flags=re.I)
    cleaned = cleaned.strip().rstrip(").,;]")
    return cleaned.lower()


def _extract_doi_from_text(text: str) -> str | None:
    if not text:
        return None
    match = re.search(
        r"(?:doi:\s*|https?://(?:dx\.)?doi\.org/)(10\.\d{4,9}/[^\s\"<>]+)",
        text,
        flags=re.I,
    )
    if match:
        return _clean_doi(match.group(1))
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text, flags=re.I)
    if match:
        return _clean_doi(match.group(0))
    return None


def _compute_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _extract_pdf_text(reader: PdfReader, max_pages: int) -> str:
    parts: list[str] = []
    for page in reader.pages[: max_pages]:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def _extract_pdf_metadata(reader: PdfReader) -> dict[str, str]:
    data: dict[str, str] = {}
    meta = getattr(reader, "metadata", None)
    if meta and isinstance(meta, dict):
        title = meta.get("/Title")
        author = meta.get("/Author")
        keywords = meta.get("/Keywords")
        created = meta.get("/CreationDate")
        if isinstance(title, str) and title.strip():
            data["title"] = title.strip()
        if isinstance(author, str) and author.strip():
            data["authors"] = author.strip()
        if isinstance(keywords, str) and keywords.strip():
            data["keywords"] = keywords.strip()
        if isinstance(created, str):
            match = re.search(r"(19|20)\d{2}", created)
            if match:
                data["year"] = match.group(0)
    return data


def _extract_title_authors_year(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    if not text:
        return data
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = ""
    for line in lines[:20]:
        lower = line.lower()
        if "doi" in lower or lower in {"abstract", "introduction"}:
            continue
        if len(line) < 5 or len(line) > 200:
            continue
        if sum(ch.isalpha() for ch in line) < 10:
            continue
        if len(line.split()) < 3:
            continue
        title = line
        break
    if title:
        data["title"] = title
        if title in lines:
            start = lines.index(title) + 1
            for line in lines[start : start + 5]:
                lower = line.lower()
                if any(word in lower for word in ("university", "department", "email", "@")):
                    continue
                if "," in line or " and " in lower:
                    data["authors"] = line
                    break
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        data["year"] = match.group(0)
    return data


def _search_doi_in_pages(reader: PdfReader, max_pages: int) -> str | None:
    total_pages = len(reader.pages)
    limit = total_pages if max_pages <= 0 else min(total_pages, max_pages)
    for index in range(limit):
        try:
            text = reader.pages[index].extract_text() or ""
        except Exception:
            continue
        doi = _extract_doi_from_text(text)
        if doi:
            return doi
    return None


def _extract_doi_from_filename(path: Path) -> str | None:
    name = path.stem.replace("_", " ").replace("-", " ")
    return _extract_doi_from_text(name)


def _extract_meta_from_filename(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    name = path.stem.replace("_", " ").replace("-", " ")
    year_match = re.search(r"(19|20)\d{2}", name)
    if year_match:
        data["year"] = year_match.group(0)
    parts = [part for part in name.split() if part]
    if parts:
        data["authors"] = parts[0]
    if len(parts) >= 3:
        data["title"] = " ".join(parts[1:])
    return data


def _safe_filename(base: str, pdf_hash: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", base)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = f"doc_{pdf_hash[:8]}"
    if len(cleaned) > 120:
        cleaned = f"{cleaned[:60]}_{pdf_hash[:8]}"
    return cleaned


def _rename_pdf(pdf_path: Path, author_last: str, year: str, pdf_hash: str) -> Path:
    directory = pdf_path.parent
    base = _safe_filename(f"{author_last}_{year}", pdf_hash)
    target = directory / f"{base}.pdf"
    if target.resolve() == pdf_path.resolve():
        return pdf_path
    if not target.exists():
        pdf_path.rename(target)
        return target
    counter = 2
    while True:
        candidate = directory / f"{base}_{counter}.pdf"
        if not candidate.exists():
            pdf_path.rename(candidate)
            return candidate
        counter += 1


def _infer_collection_from_pdf_path(path: Path) -> str:
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


def _guess_doc_type(doi: str | None, isbn: str | None, text: str) -> str:
    if isbn:
        return "book"
    if doi:
        return "article"
    lower = text.lower()
    if any(word in lower for word in ("book", "livre", "ouvrage")):
        return "book"
    if any(word in lower for word in ("article", "journal", "revue", "paper")):
        return "article"
    return "unknown"


def _is_preprint(entry: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(entry.get("journal", "")),
            str(entry.get("venue", "")),
            str(entry.get("doi", "")),
        ]
    ).lower()
    return any(tag in text for tag in ("arxiv", "biorxiv", "medrxiv", "preprint"))


class _RateLimiter:
    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < self.interval:
                time.sleep(self.interval - delta)
            self._last = time.monotonic()


class _MetadataCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, dict[str, Any]] = {
            "crossref": {},
            "semantic": {},
            "crossref_search": {},
            "semantic_search": {},
        }
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.data = {"crossref": {}, "semantic": {}, "crossref_search": {}, "semantic_search": {}}
        else:
            for key in ("crossref", "semantic", "crossref_search", "semantic_search"):
                self.data.setdefault(key, {})

    def save(self) -> None:
        try:
            with self._lock:
                payload = json.dumps(self.data, indent=2)
            self.path.write_text(payload, encoding="utf-8")
        except OSError:
            return

    def get(self, kind: str, key: str) -> dict[str, Any] | None:
        with self._lock:
            return self.data.get(kind, {}).get(key)

    def set(self, kind: str, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            if kind not in self.data:
                self.data[kind] = {}
            self.data[kind][key] = value


def _fetch_json(url: str, limiter: _RateLimiter) -> dict[str, Any] | None:
    limiter.wait()
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "motherload_projet/1.0"},
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _crossref_meta(
    doi: str,
    mailto: str | None,
    limiter: _RateLimiter,
    cache: _MetadataCache,
) -> dict[str, str]:
    cached = cache.get("crossref", doi)
    if cached is not None:
        return cached
    mail = mailto or "unknown@example.com"
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}?mailto={quote(mail, safe='')}"
    payload = _fetch_json(url, limiter)
    if not payload:
        return {}
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, dict):
        return {}
    title_value = ""
    title = message.get("title") or []
    if isinstance(title, list) and title:
        title_value = str(title[0]).strip()
    authors = []
    for author in message.get("author", []) or []:
        if not isinstance(author, dict):
            continue
        family = str(author.get("family", "")).strip()
        given = str(author.get("given", "")).strip()
        if family and given:
            authors.append(f"{family}, {given}")
        elif family or given:
            authors.append(family or given)
    year_value = ""
    for key in ("issued", "published-print", "published-online", "created"):
        issued = message.get(key, {})
        if isinstance(issued, dict):
            parts = issued.get("date-parts")
            if parts and isinstance(parts, list) and parts[0]:
                year_value = str(parts[0][0])
                break
    meta: dict[str, str] = {}
    if title_value:
        meta["title"] = title_value
    if authors:
        meta["authors"] = "; ".join(authors)
    if year_value:
        meta["year"] = year_value
    journal = message.get("container-title") or []
    if isinstance(journal, list) and journal:
        meta["journal"] = str(journal[0]).strip()
    volume = str(message.get("volume", "")).strip()
    issue = str(message.get("issue", "")).strip()
    pages = str(message.get("page", "")).strip()
    url = str(message.get("URL", "")).strip()
    if volume:
        meta["volume"] = volume
    if issue:
        meta["issue"] = issue
    if pages:
        meta["pages"] = pages
    if url:
        meta["url"] = url
    cache.set("crossref", doi, meta)
    return meta


def _semantic_meta(
    doi: str,
    fields: str,
    limiter: _RateLimiter,
    cache: _MetadataCache,
) -> dict[str, str]:
    cached = cache.get("semantic", doi)
    if cached is not None:
        return cached
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/"
        f"DOI:{quote(doi, safe='')}?fields={quote(fields, safe=',')}"
    )
    payload = _fetch_json(url, limiter)
    if not payload or not isinstance(payload, dict):
        return {}
    meta: dict[str, str] = {}
    title_value = str(payload.get("title", "")).strip()
    year_value = str(payload.get("year", "")).strip()
    if title_value:
        meta["title"] = title_value
    if year_value:
        meta["year"] = year_value
    authors = []
    for author in payload.get("authors", []) or []:
        if not isinstance(author, dict):
            continue
        name = str(author.get("name", "")).strip()
        if name:
            authors.append(name)
    if authors:
        meta["authors"] = "; ".join(authors)
    venue = str(payload.get("venue", "")).strip()
    if venue:
        meta["venue"] = venue
    journal = payload.get("journal")
    if isinstance(journal, dict):
        jname = str(journal.get("name", "")).strip()
        if jname:
            meta["journal"] = jname
    volume = str(payload.get("volume", "")).strip()
    issue = str(payload.get("issue", "")).strip()
    pages = str(payload.get("pages", "")).strip()
    if volume:
        meta["volume"] = volume
    if issue:
        meta["issue"] = issue
    if pages:
        meta["pages"] = pages
    cache.set("semantic", doi, meta)
    return meta


def _crossref_search_title(
    title: str,
    authors: str,
    year: str,
    mailto: str | None,
    limiter: _RateLimiter,
    cache: _MetadataCache,
) -> dict[str, str]:
    key = f"{title}|{authors}|{year}"
    cached = cache.get("crossref_search", key)
    if cached is not None:
        return cached
    mail = mailto or "unknown@example.com"
    query_title = quote(title, safe="")
    url = f"https://api.crossref.org/works?query.title={query_title}&rows=1&mailto={quote(mail, safe='')}"
    if authors:
        url += f"&query.author={quote(authors, safe='')}"
    if year:
        url += f"&filter=from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"
    payload = _fetch_json(url, limiter)
    if not payload:
        cache.set("crossref_search", key, {})
        return {}
    message = payload.get("message") if isinstance(payload, dict) else None
    items = message.get("items") if isinstance(message, dict) else None
    if not items:
        cache.set("crossref_search", key, {})
        return {}
    item = items[0] if isinstance(items, list) and items else None
    if not isinstance(item, dict):
        cache.set("crossref_search", key, {})
        return {}
    meta: dict[str, str] = {}
    doi = str(item.get("DOI", "")).strip()
    if doi:
        meta["doi"] = doi.lower()
    title_list = item.get("title") or []
    if isinstance(title_list, list) and title_list:
        meta["title"] = str(title_list[0]).strip()
    authors_list = []
    for author in item.get("author", []) or []:
        if not isinstance(author, dict):
            continue
        family = str(author.get("family", "")).strip()
        given = str(author.get("given", "")).strip()
        if family and given:
            authors_list.append(f"{family}, {given}")
        elif family or given:
            authors_list.append(family or given)
    if authors_list:
        meta["authors"] = "; ".join(authors_list)
    year_value = ""
    for key_date in ("issued", "published-print", "published-online", "created"):
        issued = item.get(key_date, {})
        if isinstance(issued, dict):
            parts = issued.get("date-parts")
            if parts and isinstance(parts, list) and parts[0]:
                year_value = str(parts[0][0])
                break
    if year_value:
        meta["year"] = year_value
    cache.set("crossref_search", key, meta)
    return meta


def _semantic_search_title(
    title: str,
    authors: str,
    year: str,
    fields: str,
    limiter: _RateLimiter,
    cache: _MetadataCache,
) -> dict[str, str]:
    key = f"{title}|{authors}|{year}"
    cached = cache.get("semantic_search", key)
    if cached is not None:
        return cached
    query = title
    if authors:
        query = f"{title} {authors}"
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={quote(query, safe='')}&limit=1&fields={quote(fields + ',doi', safe=',')}"
    )
    payload = _fetch_json(url, limiter)
    if not payload or not isinstance(payload, dict):
        cache.set("semantic_search", key, {})
        return {}
    data = payload.get("data") or []
    item = data[0] if isinstance(data, list) and data else None
    if not isinstance(item, dict):
        cache.set("semantic_search", key, {})
        return {}
    meta: dict[str, str] = {}
    doi = str(item.get("doi", "")).strip()
    if doi:
        meta["doi"] = doi.lower()
    title_value = str(item.get("title", "")).strip()
    if title_value:
        meta["title"] = title_value
    year_value = str(item.get("year", "")).strip()
    if year_value:
        meta["year"] = year_value
    authors_list = []
    for author in item.get("authors", []) or []:
        if not isinstance(author, dict):
            continue
        name = str(author.get("name", "")).strip()
        if name:
            authors_list.append(name)
    if authors_list:
        meta["authors"] = "; ".join(authors_list)
    venue = str(item.get("venue", "")).strip()
    if venue:
        meta["venue"] = venue
    journal = item.get("journal")
    if isinstance(journal, dict):
        jname = str(journal.get("name", "")).strip()
        if jname:
            meta["journal"] = jname
    volume = str(item.get("volume", "")).strip()
    issue = str(item.get("issue", "")).strip()
    pages = str(item.get("pages", "")).strip()
    if volume:
        meta["volume"] = volume
    if issue:
        meta["issue"] = issue
    if pages:
        meta["pages"] = pages
    cache.set("semantic_search", key, meta)
    return meta


def _grobid_header(
    pdf_path: Path,
    grobid_url: str,
    limiter: _RateLimiter,
) -> dict[str, str]:
    endpoint = grobid_url.rstrip("/") + "/api/processHeaderDocument"
    limiter.wait()
    try:
        with pdf_path.open("rb") as handle:
            response = requests.post(endpoint, files={"input": handle}, timeout=30)
    except requests.RequestException:
        return {}
    if response.status_code != 200:
        return {}
    text = response.text
    meta: dict[str, str] = {}
    title_match = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    if title_match:
        meta["title"] = re.sub(r"\s+", " ", title_match.group(1)).strip()
    return meta


def _ocr_text(pdf_path: Path, max_pages: int, lang: str) -> str:
    tool = shutil.which("tesseract")
    if not tool:
        return ""
    temp_dir = Path(os.getenv("TMPDIR", "/tmp")) / f"momo_ocr_{pdf_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    images: list[Path] = []
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        return ""
    output_base = temp_dir / "page"
    subprocess.run(
        [
            pdftoppm,
            "-f",
            "1",
            "-l",
            str(max_pages),
            "-png",
            str(pdf_path),
            str(output_base),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for image in temp_dir.glob("page-*.png"):
        images.append(image)
    texts: list[str] = []
    for image in images:
        out_base = image.with_suffix("")
        subprocess.run(
            [tool, str(image), str(out_base), "-l", lang],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        txt_file = out_base.with_suffix(".txt")
        if txt_file.exists():
            try:
                texts.append(txt_file.read_text(encoding="utf-8"))
            except OSError:
                continue
    return "\n".join(texts)


def _merge_fields(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        current = str(target.get(key, "")).strip()
        if not current:
            target[key] = value


def _process_pdf(
    pdf_path: Path,
    cfg: ScanConfig,
    limiter: _RateLimiter,
    cache: _MetadataCache,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return {"entry": None, "warnings": warnings, "errors": ["PARSE_FAIL"], "pdf_path": str(pdf_path)}

    file_hash = _compute_hash(pdf_path)
    meta = _extract_pdf_metadata(reader)
    text = _extract_pdf_text(reader, cfg.max_pages_text)

    doi = _extract_doi_from_text(text)
    if not doi:
        doi = _search_doi_in_pages(reader, cfg.max_pages_doi)
    if not doi:
        doi = _extract_doi_from_filename(pdf_path)
    if not doi:
        warnings.append("DOI_NOT_FOUND")

    isbn = _extract_isbn_from_text(text)
    if not isbn:
        isbn = _extract_isbn_from_text(pdf_path.stem.replace("_", " ").replace("-", " "))

    if cfg.enable_ocr and (not text or (not doi and not isbn)):
        ocr_text = _ocr_text(pdf_path, cfg.max_pages_ocr, cfg.ocr_lang)
        if ocr_text:
            text = (text + "\n" + ocr_text).strip()
            if not doi:
                doi = _extract_doi_from_text(ocr_text)
            if not isbn:
                isbn = _extract_isbn_from_text(ocr_text)
        else:
            warnings.append("OCR_FAIL")

    doc_type = _guess_doc_type(doi, isbn, text)

    entry = {
        "file_hash": file_hash,
        "pdf_path": str(pdf_path),
        "doi": doi or "",
        "isbn": isbn or "",
        "title": meta.get("title", "") or pdf_path.stem,
        "authors": meta.get("authors", ""),
        "keywords": meta.get("keywords", ""),
        "year": meta.get("year", ""),
        "type": doc_type,
        "journal": "",
        "venue": "",
        "volume": "",
        "issue": "",
        "pages": "",
        "url": "",
    }

    # heuristiques locales
    heur = _extract_title_authors_year(text)
    _merge_fields(entry, heur)

    # enrichissement avec DOI
    if entry.get("doi"):
        crossref_meta = _crossref_meta(entry["doi"], cfg.crossref_mailto, limiter, cache)
        if not crossref_meta:
            warnings.append("CROSSREF_FAIL")
        semantic_meta = _semantic_meta(entry["doi"], cfg.semantic_fields, limiter, cache)
        if not semantic_meta:
            warnings.append("SEMANTIC_FAIL")
        _merge_fields(entry, crossref_meta)
        _merge_fields(entry, semantic_meta)

    # Grobid (optionnel)
    if cfg.enable_grobid and cfg.grobid_url:
        grobid_meta = _grobid_header(pdf_path, cfg.grobid_url, limiter)
        if grobid_meta:
            _merge_fields(entry, grobid_meta)
        else:
            warnings.append("GROBID_FAIL")

    # Recherche titre si DOI absent
    if not entry.get("doi") and entry.get("title"):
        search_meta = _crossref_search_title(
            entry.get("title", ""),
            entry.get("authors", ""),
            entry.get("year", ""),
            cfg.crossref_mailto,
            limiter,
            cache,
        )
        if search_meta:
            _merge_fields(entry, search_meta)
        else:
            warnings.append("CROSSREF_SEARCH_FAIL")

    if not entry.get("doi") and entry.get("title"):
        semantic_search = _semantic_search_title(
            entry.get("title", ""),
            entry.get("authors", ""),
            entry.get("year", ""),
            cfg.semantic_fields,
            limiter,
            cache,
        )
        if semantic_search:
            _merge_fields(entry, semantic_search)
        else:
            warnings.append("SEMANTIC_SEARCH_FAIL")

    # Metadonnees depuis le nom de fichier
    filename_meta = _extract_meta_from_filename(pdf_path)
    _merge_fields(entry, filename_meta)

    # Re-enrichissement DOI si trouve par recherche
    if entry.get("doi") and not entry.get("journal"):
        crossref_meta = _crossref_meta(entry["doi"], cfg.crossref_mailto, limiter, cache)
        _merge_fields(entry, crossref_meta)

    # Ajuste type si besoin
    if entry.get("isbn"):
        entry["type"] = "book"
    elif entry.get("doi"):
        entry["type"] = "article"

    if not (str(entry.get("title", "")).strip() and str(entry.get("authors", "")).strip() and str(entry.get("year", "")).strip()):
        warnings.append("MISSING_CORE")

    return {"entry": entry, "warnings": warnings, "errors": errors, "pdf_path": str(pdf_path)}

def _build_index(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    index = {"doi": {}, "isbn": {}, "fingerprint": {}, "file_hash": {}}
    for idx, row in df.iterrows():
        doi = str(row.get("doi", "")).strip().lower()
        isbn = str(row.get("isbn", "")).strip()
        fp = str(row.get("fingerprint", "")).strip()
        fh = str(row.get("file_hash", "")).strip()
        if doi:
            index["doi"].setdefault(doi, idx)
        if isbn:
            index["isbn"].setdefault(isbn, idx)
        if fp:
            index["fingerprint"].setdefault(fp, idx)
        if fh:
            index["file_hash"].setdefault(fh, idx)
    return index


def _find_match(entry: dict[str, Any], index: dict[str, dict[str, int]]) -> int | None:
    doi = str(entry.get("doi", "")).strip().lower()
    isbn = str(entry.get("isbn", "")).strip()
    fp = str(entry.get("fingerprint", "")).strip()
    fh = str(entry.get("file_hash", "")).strip()
    if doi and doi in index["doi"]:
        return index["doi"][doi]
    if isbn and isbn in index["isbn"]:
        return index["isbn"][isbn]
    if fp and fp in index["fingerprint"]:
        return index["fingerprint"][fp]
    if fh and fh in index["file_hash"]:
        return index["file_hash"][fh]
    return None


def _update_index(index: dict[str, dict[str, int]], row: dict[str, Any], idx: int) -> None:
    doi = str(row.get("doi", "")).strip().lower()
    isbn = str(row.get("isbn", "")).strip()
    fp = str(row.get("fingerprint", "")).strip()
    fh = str(row.get("file_hash", "")).strip()
    if doi:
        index["doi"][doi] = idx
    if isbn:
        index["isbn"][isbn] = idx
    if fp:
        index["fingerprint"][fp] = idx
    if fh:
        index["file_hash"][fh] = idx


def _fill_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Complete primary_id et fingerprint si manquants."""
    df = df.copy()
    for idx, row in df.iterrows():
        current_fp = str(row.get("fingerprint", "")).strip()
        if not current_fp:
            fp = fingerprint(row.get("title"), row.get("authors"), row.get("year"))
            df.at[idx, "fingerprint"] = fp
        current_pid = str(row.get("primary_id", "")).strip()
        if not current_pid:
            pid = primary_id(row.get("doi"), row.get("isbn"), df.at[idx, "fingerprint"], row.get("file_hash"))
            df.at[idx, "primary_id"] = pid
    return df


def _resolve_version(entry: dict[str, Any]) -> str:
    if _is_preprint(entry):
        return "preprint"
    return "final" if entry.get("doi") else ""


def _apply_preprint_replacements(df: pd.DataFrame) -> pd.DataFrame:
    """Marque les preprints remplaces par la version finale."""
    df = df.copy()
    df = _ensure_columns(df, ["replaced_by", "version", "primary_id", "fingerprint"])
    groups: dict[str, list[tuple[int, pd.Series]]] = {}
    for idx, row in df.iterrows():
        fp = str(row.get("fingerprint", "")).strip()
        if not fp:
            continue
        groups.setdefault(fp, []).append((idx, row))
    for _, items in groups.items():
        finals = [item for item in items if str(item[1].get("version", "")) == "final"]
        preprints = [item for item in items if str(item[1].get("version", "")) == "preprint"]
        if finals and preprints:
            final_id = str(finals[0][1].get("primary_id", "")).strip()
            for idx, _row in preprints:
                df.at[idx, "replaced_by"] = final_id
    return df


def scan_library(
    pdf_root: Path | None = None,
    cfg: ScanConfig | None = None,
    progress_cb: Any | None = None,
    export_catalogs_flag: bool = True,
    export_bib_flag: bool = False,
) -> dict[str, Any]:
    """Scanne la bibliotheque et met a jour les catalogues."""
    pdf_root = Path(pdf_root) if pdf_root else (library_root() / "pdfs")
    if not pdf_root.exists():
        return {"error": "PDF_ROOT_MISSING"}

    cfg = cfg or ScanConfig()
    cfg.crossref_mailto = cfg.crossref_mailto or get_crossref_email() or get_unpaywall_email()
    cache_path = cfg.cache_path or (bibliotheque_root() / "scan_cache.json")
    cache = _MetadataCache(cache_path)
    limiter = _RateLimiter(cfg.rate_limit_sec)

    master_path = ensure_dir(bibliotheque_root()) / "master_catalog.csv"
    master_df = load_master_catalog(master_path)
    master_df = _ensure_columns(master_df, DEFAULT_SCAN_COLUMNS)

    index = _build_index(master_df)

    pdf_paths = [path for path in pdf_root.rglob("*.pdf") if path.is_file()]
    total = len(pdf_paths)
    final_pdf_paths: list[str] = []

    created = 0
    updated = 0
    matched = 0
    processed = 0
    errors = 0
    warnings = 0
    error_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}

    scan_tag = _timestamp_tag()

    def _bump(counter: dict[str, int], key: str) -> None:
        counter[key] = counter.get(key, 0) + 1

    with ThreadPoolExecutor(max_workers=max(1, cfg.max_workers)) as executor:
        future_map = {
            executor.submit(_process_pdf, path, cfg, limiter, cache): path
            for path in pdf_paths
        }
        done_count = 0
        for future in as_completed(future_map):
            done_count += 1
            path = future_map[future]
            if progress_cb:
                progress_cb({"stage": "item", "done": done_count, "total": total, "path": str(path)})
            result = future.result()
            processed += 1
            for warn in result.get("warnings", []):
                warnings += 1
                _bump(warning_counts, warn)
            for err in result.get("errors", []):
                errors += 1
                _bump(error_counts, err)
            entry = result.get("entry")
            if not entry:
                continue

            file_hash = str(entry.get("file_hash", "")).strip()
            author_last = first_author_last(entry.get("authors"))
            year_value = str(entry.get("year", "")).strip() or "0000"
            renamed_path = _rename_pdf(Path(entry["pdf_path"]), author_last, year_value, file_hash)
            if renamed_path:
                entry["pdf_path"] = str(renamed_path)
            entry["collection"] = _infer_collection_from_pdf_path(Path(entry["pdf_path"]))
            entry["fingerprint"] = fingerprint(entry.get("title"), entry.get("authors"), entry.get("year"))
            entry["primary_id"] = primary_id(
                entry.get("doi"), entry.get("isbn"), entry.get("fingerprint"), entry.get("file_hash")
            )
            entry["version"] = _resolve_version(entry)
            final_pdf_paths.append(entry["pdf_path"])

            match_idx = _find_match(entry, index)
            if match_idx is None:
                new_record = {name: "" for name in master_df.columns}
                _merge_fields(new_record, entry)
                new_record["collection"] = entry.get("collection", "")
                master_df = pd.concat([master_df, pd.DataFrame([new_record])], ignore_index=True)
                new_idx = len(master_df) - 1
                _update_index(index, new_record, new_idx)
                created += 1
            else:
                matched += 1
                current = master_df.loc[match_idx].to_dict()
                merged = current.copy()
                _merge_fields(merged, entry)
                if merged.get("type") in {"", "unknown"} and entry.get("type"):
                    merged["type"] = entry.get("type")
                for key, value in merged.items():
                    master_df.at[match_idx, key] = value
                updated += 1

    cache.save()

    master_df = _fill_identifiers(master_df)
    # preprint vs final
    master_df = _apply_preprint_replacements(master_df)

    cfg_complete = CompletenessConfig()
    complete_rows = []
    for _, row in master_df.iterrows():
        if row.get("replaced_by"):
            continue
        if not row.get("pdf_path") and not row.get("file_hash"):
            continue
        if is_complete(row.to_dict(), cfg_complete):
            complete_rows.append(row)
    complete_df = pd.DataFrame(complete_rows) if complete_rows else master_df.head(0).copy()

    outputs: dict[str, str] = {}
    if export_catalogs_flag:
        outputs.update(export_catalogs(master_df, complete_df, bibliotheque_root()))

    reports = write_reports(master_df, final_pdf_paths, reports_root(), cfg_complete)

    if export_bib_flag:
        bib_path = bibliotheque_root() / "export_master.bib"
        export_bibtex(master_df, bib_path)
        outputs["bibtex"] = str(bib_path)

    master_df.to_csv(master_path, index=False)

    summary = ScanRunSummary(
        timestamp=scan_tag,
        total_pdfs=total,
        processed_pdfs=processed,
        created=created,
        updated=updated,
        matched=matched,
        errors=errors,
        warnings=warnings,
        error_counts=error_counts,
        warning_counts=warning_counts,
        reports=reports,
        outputs=outputs,
    )

    scan_runs_dir = ensure_dir(bibliotheque_root() / "scan_runs")
    run_path = scan_runs_dir / f"{scan_tag}.json"
    run_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")

    latest_path = scan_runs_dir / "latest.json"
    latest = {"runs": []}
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {"runs": []}
    runs = latest.get("runs", [])
    runs.insert(0, {"timestamp": scan_tag, "path": str(run_path)})
    latest["runs"] = runs[:2]
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")

    return summary.to_dict()
