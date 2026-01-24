"""Client Unpaywall."""

from __future__ import annotations

from typing import Any

import requests


class UnpaywallError(RuntimeError):
    """Erreur Unpaywall."""


def fetch_unpaywall_record(doi: str, email: str, timeout: int = 30) -> dict[str, Any]:
    """Recupere un enregistrement Unpaywall."""
    if not doi:
        raise UnpaywallError("DOI manquant")
    if not email:
        raise UnpaywallError("UNPAYWALL_EMAIL manquant")

    url = f"https://api.unpaywall.org/v2/{doi}"
    try:
        response = requests.get(url, params={"email": email}, timeout=timeout)
    except requests.Timeout as exc:
        raise UnpaywallError("Unpaywall timeout") from exc
    except requests.RequestException as exc:
        raise UnpaywallError("Unpaywall erreur reseau") from exc

    if response.status_code != 200:
        raise UnpaywallError(f"Unpaywall status {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        raise UnpaywallError("Unpaywall reponse invalide") from exc


def extract_pdf_candidates(record: dict[str, Any]) -> list[dict[str, str]]:
    """Extrait les URLs candidates."""
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    def _add(url: str | None, kind: str) -> None:
        if not url or url in seen:
            return
        seen.add(url)
        candidates.append({"url": url, "kind": kind})

    best_location = record.get("best_oa_location")
    if isinstance(best_location, dict):
        _add(best_location.get("url_for_pdf"), "pdf")

    locations = record.get("oa_locations")
    if isinstance(locations, list):
        for location in locations:
            if isinstance(location, dict):
                _add(location.get("url_for_pdf"), "pdf")

    if isinstance(best_location, dict):
        _add(best_location.get("url"), "landing")

    if isinstance(locations, list):
        for location in locations:
            if isinstance(location, dict):
                _add(location.get("url"), "landing")

    return candidates
