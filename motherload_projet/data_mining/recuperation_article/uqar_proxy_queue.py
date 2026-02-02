"""Workflow proxy UQAR (export + ouverture)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
import webbrowser
from urllib.parse import quote_plus

import pandas as pd

from motherload_projet.config import get_manual_import_subdir, get_uqar_ezproxy_prefix
from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root

DISCOVERY_BASE_URL = "https://uqar-on-worldcat-org.ezproxy.uqar.ca/discovery"


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


def _default_notes(manual_subdir: str) -> str:
    """Retourne les notes par defaut."""
    return (
        "Ouvrir le lien, chercher DOI ou titre, "
        "cliquer 'Acces en ligne', "
        f"telecharger le PDF, deposer dans {manual_subdir}/."
    )


def _build_search_url(query_text: str) -> str:
    """Construit un lien de recherche."""
    query = quote_plus(query_text)
    return f"{DISCOVERY_BASE_URL}/search?queryString={query}"


def _build_proxy_search_url(prefix: str | None, query_text: str) -> str:
    """Construit un lien EZproxy."""
    if not prefix or not query_text:
        return ""
    return f"{prefix}{_build_search_url(query_text)}"


def _build_query_text(doi: str, title: str, year: str) -> str:
    """Construit le texte de recherche."""
    if doi:
        return doi
    parts = [title, year]
    return " ".join(part for part in parts if part).strip()


def _ensure_status_column(df: pd.DataFrame) -> None:
    """Garantit la colonne status."""
    if "status" not in df.columns:
        df["status"] = "pending"
        return
    df["status"] = df["status"].fillna("").astype(str)
    df["status"] = df["status"].where(df["status"].str.strip() != "", "pending")


def _resolve_proxy_url_column(df: pd.DataFrame) -> str:
    """Retourne la colonne URL a utiliser."""
    if "proxy_search_url" in df.columns:
        return "proxy_search_url"
    if "uqar_discovery_url" in df.columns:
        df["proxy_search_url"] = df["uqar_discovery_url"].fillna("")
        return "proxy_search_url"
    df["proxy_search_url"] = ""
    return "proxy_search_url"


def export_proxy_queue(source_csv: Path | str) -> dict[str, Path | bool | str]:
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

    df["query_text"] = df.apply(
        lambda row: _build_query_text(
            _clean_text(row.get("doi", "")),
            _clean_text(row.get("title", "")),
            _clean_text(row.get("year", "")),
        ),
        axis=1,
    )

    prefix = get_uqar_ezproxy_prefix()
    links_enabled = bool(prefix)
    df["proxy_search_url"] = df["query_text"].apply(
        lambda text: _build_proxy_search_url(prefix, text)
    )
    _ensure_status_column(df)
    manual_subdir = get_manual_import_subdir()
    df["notes"] = _default_notes(manual_subdir)

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
        "proxy_search_url",
        "status",
        "notes",
    ]
    df[columns].to_csv(proxy_queue_path, index=False)

    reason_counts = Counter([reason for reason in df["reason_code"] if reason])
    link_state = "OK" if links_enabled else "MANQUANT"
    report_lines = [
        "Proxy queue report",
        f"Source: {source_csv}",
        f"Total items: {len(df)}",
        f"EZproxy prefix: {link_state}",
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
            f"- Deposer les PDFs dans: ~/Desktop/grand_librairy/pdfs/<collection>/{manual_subdir}/",
            "- Ingest: python -m motherload_projet.cli --uqar-proxy-ingest",
            "- Ouvrir un lien: python -m motherload_projet.cli --uqar-proxy-open",
            "Fichiers:",
            f"- Proxy queue: {proxy_queue_path}",
            f"- Rapport: {report_path}",
        ]
    )
    if not links_enabled:
        report_lines.append(
            "ERREUR: UQAR_EZPROXY_PREFIX manquant (liens non generes)."
        )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "proxy_queue_path": proxy_queue_path,
        "report_path": report_path,
        "links_enabled": links_enabled,
        "message": (
            "ERREUR: UQAR_EZPROXY_PREFIX manquant (voir .env.example). "
            "Liens non generes."
            if not links_enabled
            else ""
        ),
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
    _ensure_status_column(df)
    url_column = _resolve_proxy_url_column(df)
    if "doi" not in df.columns:
        df["doi"] = ""
    if "title" not in df.columns:
        df["title"] = ""

    statuses = df["status"].fillna("").astype(str).str.strip().str.lower()
    remaining_mask = ~statuses.isin({"open", "downloaded"})
    if not remaining_mask.any():
        print("Aucun lien restant dans la proxy_queue.")
        return 0

    index = None
    for idx in df.index[remaining_mask]:
        candidate_url = _clean_text(df.at[idx, url_column])
        if candidate_url:
            index = idx
            break
    if index is None:
        print("ERREUR: proxy_search_url manquant (verifiez UQAR_EZPROXY_PREFIX).")
        return 2

    row = df.loc[index]
    url = _clean_text(row.get(url_column, ""))

    doi = _clean_text(row.get("doi", ""))
    title = _clean_text(row.get("title", ""))
    label = doi or title or "<sans titre>"
    print(f"Ouverture: {label}")
    print(f"URL: {url}")
    webbrowser.open(url)
    df.at[index, "status"] = "open"
    df.to_csv(queue_path, index=False)
    return 0
