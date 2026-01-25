"""Resolution Unpaywall."""

from __future__ import annotations

from typing import Any

from motherload_projet.config import get_unpaywall_email
from motherload_projet.oa.unpaywall_client import (
    UnpaywallError,
    extract_pdf_candidates,
    fetch_unpaywall_record,
)


def resolve_pdf_urls_from_unpaywall(doi: str) -> dict[str, Any]:
    """Resout des URLs candidates."""
    email = get_unpaywall_email()
    if not email:
        return {
            "doi": doi,
            "candidates": [],
            "source": "unpaywall",
            "status": "error",
            "error": "UNPAYWALL_EMAIL manquant (voir .env.example)",
            "is_oa": None,
            "oa_status": None,
            "url_for_pdf": None,
        }

    try:
        record = fetch_unpaywall_record(doi, email)
    except UnpaywallError as exc:
        return {
            "doi": doi,
            "candidates": [],
            "source": "unpaywall",
            "status": "error",
            "error": str(exc),
            "is_oa": None,
            "oa_status": None,
            "url_for_pdf": None,
        }

    candidates = extract_pdf_candidates(record)
    status = "ok" if candidates else "no_candidates"
    is_oa = record["is_oa"] if "is_oa" in record else None
    oa_status = record["oa_status"] if "oa_status" in record else None
    best_location = record.get("best_oa_location")
    url_for_pdf = None
    if isinstance(best_location, dict):
        url_for_pdf = best_location.get("url_for_pdf")
    if not url_for_pdf:
        for candidate in candidates:
            if candidate.get("kind") == "pdf":
                url_for_pdf = candidate.get("url")
                break
    return {
        "doi": doi,
        "candidates": candidates,
        "source": "unpaywall",
        "status": status,
        "error": None,
        "is_oa": is_oa,
        "oa_status": oa_status,
        "url_for_pdf": url_for_pdf,
    }
