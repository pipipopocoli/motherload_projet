"""Regles de scoring et normalisation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class CompletenessConfig:
    """Regles de completude."""

    require_common_fields: tuple[str, ...] = ("title", "authors", "year")
    article_requires_doi_or_venue: bool = True
    book_requires_isbn_or_url: bool = True


def normalize_text(value: Any) -> str:
    """Normalise un texte."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()


def normalize_author(value: str) -> str:
    """Normalise un auteur."""
    text = normalize_text(value)
    if not text:
        return ""
    parts = [part for part in text.split() if part]
    return " ".join(parts)


def first_author_last(authors: Any) -> str:
    """Extrait le nom du premier auteur."""
    if not authors:
        return "Unknown"
    text = str(authors)
    if ";" in text:
        first = text.split(";", 1)[0]
    elif " and " in text:
        first = text.split(" and ", 1)[0]
    else:
        first = text
    first = first.strip()
    if not first:
        return "Unknown"
    if "," in first:
        last = first.split(",", 1)[0].strip()
        return last or "Unknown"
    parts = [part for part in first.split() if part]
    if not parts:
        return "Unknown"
    return parts[-1]


def fingerprint(title: Any, authors: Any, year: Any) -> str:
    """Calcule un fingerprint stable."""
    title_norm = normalize_text(title)
    author_last = normalize_text(first_author_last(authors))
    year_norm = normalize_text(year)
    if not (title_norm or author_last or year_norm):
        return ""
    return f"{title_norm}|{author_last}|{year_norm}"


def primary_id(doi: Any, isbn: Any, fp: Any, pdf_hash: Any) -> str:
    """Genere un identifiant primaire."""
    if doi:
        return f"doi:{str(doi).strip().lower()}"
    if isbn:
        return f"isbn:{str(isbn).strip()}"
    if fp:
        return f"fp:{str(fp).strip()}"
    if pdf_hash:
        return f"hash:{str(pdf_hash).strip()}"
    return ""


def _has_all(entry: dict[str, Any], fields: tuple[str, ...]) -> bool:
    for name in fields:
        value = str(entry.get(name, "")).strip()
        if not value:
            return False
    return True


def is_article_complete(entry: dict[str, Any], cfg: CompletenessConfig) -> bool:
    """Verifie la completude article."""
    if not _has_all(entry, cfg.require_common_fields):
        return False
    doi = str(entry.get("doi", "")).strip()
    if doi:
        return True
    if not cfg.article_requires_doi_or_venue:
        return True
    journal = str(entry.get("journal", "")).strip() or str(entry.get("venue", "")).strip()
    volume = str(entry.get("volume", "")).strip()
    issue = str(entry.get("issue", "")).strip()
    pages = str(entry.get("pages", "")).strip()
    return bool(journal and volume and issue and pages)


def is_book_complete(entry: dict[str, Any], cfg: CompletenessConfig) -> bool:
    """Verifie la completude livre."""
    if not _has_all(entry, cfg.require_common_fields):
        return False
    isbn = str(entry.get("isbn", "")).strip()
    url = str(entry.get("url", "")).strip()
    if cfg.book_requires_isbn_or_url:
        return bool(isbn or url)
    return True


def is_complete(entry: dict[str, Any], cfg: CompletenessConfig) -> bool:
    """Verifie la completude."""
    doc_type = str(entry.get("type", "")).strip().lower()
    if doc_type == "book":
        return is_book_complete(entry, cfg)
    if doc_type == "article":
        return is_article_complete(entry, cfg)
    return False
