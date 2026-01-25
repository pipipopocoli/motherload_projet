"""Workflow proxy UQAR (export + ouverture)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import webbrowser

import pandas as pd
import requests

from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root

DEFAULT_DISCOVERY_BASE_URL = "https://uqar-on-worldcat-org.ezproxy.uqar.ca/discovery"
DEFAULT_NOTES = (
    "Ouvrir le lien, chercher DOI ou titre, "
    "cliquer 'Acces en ligne', "
    "telecharger le PDF, deposer dans manual_import/."
)


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


def _extract_tag(source_path: Path) -> str:
    """Extrait un tag depuis un fichier de run."""
    stem = source_path.stem
    for prefix in ("to_be_downloaded_", "bibliotheque_", "proxy_queue_"):
        if stem.startswith(prefix):
            return stem[len(prefix) :]
    return _timestamp_tag()


def _latest_csv(bib_root: Path, pattern: str) -> Path | None:
    """Trouve le dernier CSV par pattern."""
    candidates = list(bib_root.glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def latest_to_be_downloaded(bib_root: Path | None = None) -> Path | None:
    """Retourne le dernier to_be_downloaded."""
    bib_root = ensure_dir(bib_root or bibliotheque_root())
    return _latest_csv(bib_root, "to_be_downloaded_*.csv")


def latest_proxy_queue(bib_root: Path | None = None) -> Path | None:
    """Retourne le dernier proxy_queue."""
    bib_root = ensure_dir(bib_root or bibliotheque_root())
    return _latest_csv(bib_root, "proxy_queue_*.csv")


def _clean_text(value: Any) -> str:
    """Nettoie un champ texte."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return text


def _build_search_url(base_url: str, query_text: str) -> str:
    """Construit un lien de recherche."""
    base = base_url.rstrip("/")
    query = quote_plus(query_text)
    return f"{base}/search?queryString={query}"


def _check_search_available(base_url: str, query_text: str) -> bool:
    """Teste si le /search repond."""
    if not query_text:
        return False
    url = _build_search_url(base_url, query_text)
    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        return False
    return response.status_code == 200


def export_proxy_queue(
    source_csv: Path | str,
    discovery_base_url: str = DEFAULT_DISCOVERY_BASE_URL,
) -> dict[str, Path | bool]:
    """Exporte une proxy_queue."""
    source_csv = Path(source_csv).expanduser()
    df = pd.read_csv(source_csv)
    df = df.copy()

    for name in [
        "doi",
        "title",
        "year",
        "type",
        "authors",
        "keywords",
        "reason_code",
        "collection",
    ]:
        if name not in df.columns:
            df[name] = ""
        df[name] = df[name].apply(_clean_text)

    df["query_text"] = df["doi"].where(df["doi"] != "", df["title"]).apply(_clean_text)
    sample_query = ""
    for value in df["query_text"]:
        if value:
            sample_query = value
            break
    search_ok = _check_search_available(discovery_base_url, sample_query)

    def _resolve_url(query_text: str) -> str:
        if search_ok and query_text:
            return _build_search_url(discovery_base_url, query_text)
        return discovery_base_url

    df["uqar_discovery_url"] = df["query_text"].apply(_resolve_url)
    df["notes"] = DEFAULT_NOTES

    tag = _extract_tag(source_csv)
    bib_root = ensure_dir(bibliotheque_root())
    reports_dir = ensure_dir(reports_root())
    proxy_queue_path = _unique_path(bib_root / f"proxy_queue_{tag}.csv")
    report_path = _unique_path(reports_dir / f"proxy_queue_report_{tag}.txt")

    columns = [
        "doi",
        "title",
        "year",
        "type",
        "authors",
        "keywords",
        "reason_code",
        "collection",
        "query_text",
        "uqar_discovery_url",
        "notes",
    ]
    df[columns].to_csv(proxy_queue_path, index=False)

    reason_counts = Counter([reason for reason in df["reason_code"] if reason])
    report_lines = [
        "Proxy queue report",
        f"Source: {source_csv}",
        f"Total items: {len(df)}",
        f"Search link: {'OK' if search_ok else 'base_url only'}",
        "Reasons:",
    ]
    if reason_counts:
        for reason, count in reason_counts.most_common():
            report_lines.append(f"- {reason}: {count}")
    else:
        report_lines.append("- aucune")
    report_lines.extend(
        [
            "Manual import:",
            "- Deposer les PDFs dans: ~/Desktop/grand_librairy/pdfs/<collection>/manual_import/",
            "- Ingest: python -m motherload_projet.cli --uqar-proxy-ingest",
            "Fichiers:",
            f"- Proxy queue: {proxy_queue_path}",
            f"- Rapport: {report_path}",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "proxy_queue_path": proxy_queue_path,
        "report_path": report_path,
        "search_ok": search_ok,
    }


def open_proxy_queue(queue_path: Path | str) -> int:
    """Ouvre un lien de proxy_queue."""
    queue_path = Path(queue_path).expanduser()
    try:
        df = pd.read_csv(queue_path)
    except Exception as exc:
        print(f"Erreur lecture proxy_queue: {exc}")
        return 2

    if df.empty:
        print("Proxy queue vide.")
        return 0

    df = df.copy()
    if "uqar_discovery_url" not in df.columns:
        df["uqar_discovery_url"] = DEFAULT_DISCOVERY_BASE_URL
    if "doi" not in df.columns:
        df["doi"] = ""
    if "title" not in df.columns:
        df["title"] = ""

    total = len(df)
    display_count = min(total, 20)
    print(f"Proxy queue: {queue_path}")
    for index in range(display_count):
        row = df.iloc[index]
        doi = _clean_text(row.get("doi", ""))
        title = _clean_text(row.get("title", ""))
        label = doi or title or "<sans titre>"
        print(f"{index + 1}) {label}")
    if total > display_count:
        print(f"... ({total - display_count} autres)")

    while True:
        try:
            choice = input("Choix (numero, q=quit): ").strip()
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if not choice:
            continue
        lowered = choice.lower()
        if lowered == "q":
            return 0
        if not choice.isdigit():
            print("Choix invalide.")
            continue
        index = int(choice) - 1
        if index < 0 or index >= total:
            print("Choix invalide.")
            continue
        row = df.iloc[index]
        url = _clean_text(row.get("uqar_discovery_url", "")) or DEFAULT_DISCOVERY_BASE_URL
        print(f"Ouverture: {url}")
        webbrowser.open(url)
        return 0
