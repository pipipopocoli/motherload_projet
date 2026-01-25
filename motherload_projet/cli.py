"""Point d entree du CLI."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

from motherload_projet.config import get_openalex_key, get_unpaywall_email
from motherload_projet.library.paths import (
    archives_root,
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
    reports_root,
)
from motherload_projet.oa.resolver import resolve_pdf_urls_from_unpaywall
from motherload_projet.reporting.summary import write_report
from motherload_projet.ui.collections_menu import choose_collection
from motherload_projet.ui.csv_navigator import select_csv, was_cancelled_by_interrupt
from motherload_projet.workflow.run_unpaywall_batch import (
    attempt_unpaywall_download,
    run_unpaywall_csv_batch,
    run_unpaywall_demo_batch,
    run_unpaywall_queue,
)
from motherload_projet.workflow.uqar_proxy_ingest import (
    infer_run_csv_path,
    ingest_manual_pdfs,
    manual_import_dir_for_collection,
    resolve_collection_for_ingest,
)
from motherload_projet.workflow.uqar_proxy_queue import (
    export_proxy_queue,
    latest_proxy_queue,
    latest_to_be_downloaded,
    open_proxy_queue,
)

UNPAYWALL_DEMO_DOIS = [
    "10.7717/peerj.4375",
    "10.1371/journal.pone.0259580",
    "10.7554/eLife.110158",
]
UNPAYWALL_MIN_PDF_KB = 100


def _demo_dataframe() -> pd.DataFrame:
    """Cree un DataFrame de demo."""
    rows = [
        {
            "title": "Demo Title 1",
            "authors": "Alice Doe; Bob Roe",
            "doi": "10.1234/demo1",
            "isbn": "9780000000001",
            "type": "article",
            "keywords": "demo; test",
        },
        {
            "title": "Demo Title 2",
            "authors": "Cara Poe",
            "doi": "10.1234/demo2",
            "isbn": "9780000000002",
            "type": "book",
            "keywords": "sample; catalog",
        },
        {
            "title": "Demo Title 3",
            "authors": "Dan Moe",
            "doi": "10.1234/demo3",
            "isbn": "9780000000003",
            "type": "report",
            "keywords": "example; metadata",
        },
    ]
    columns = ["title", "authors", "doi", "isbn", "type", "keywords"]
    return pd.DataFrame(rows, columns=columns)


def _make_sample_csv() -> int:
    """Cree un CSV de test."""
    rows = [
        {
            "type": "article",
            "title": "Sample Article 1",
            "doi": "10.1371/journal.pone.0259580",
            "authors": "Alice Doe; Bob Roe",
            "year": "2021",
            "keywords": "sample; oa",
        },
        {
            "type": "article",
            "title": "Sample Article 2",
            "doi": "10.7717/peerj.4375",
            "authors": "Cara Poe",
            "year": "2018",
            "keywords": "sample; peerj",
        },
        {
            "type": "article",
            "title": "Sample Article 3",
            "doi": "10.1038/nphys1170",
            "authors": "Dan Moe",
            "year": "2008",
            "keywords": "sample; physics",
        },
    ]
    path = Path.home() / "Desktop" / "motherload_sample.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["type", "title", "doi", "authors", "year", "keywords"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(path)
    return 0


def _run_oa_smoke() -> int:
    """Verifie la config OA sans reseau."""
    unpaywall_email = get_unpaywall_email()
    if not unpaywall_email:
        print("ERREUR: UNPAYWALL_EMAIL manquant (voir .env.example)")
        return 2

    print("OA smoke ready (Unpaywall)")
    if not get_openalex_key():
        print("OpenAlex: skipped (no key)")
    return 0


def _run_unpaywall_dry_run(doi_override: str | None) -> int:
    """Execute un dry-run Unpaywall."""
    dois = [doi_override] if doi_override else UNPAYWALL_DEMO_DOIS
    for doi in dois:
        result = resolve_pdf_urls_from_unpaywall(doi)
        if result.get("status") == "error":
            candidates: list[dict[str, str]] = []
            status = "error"
        else:
            candidates = [
                candidate
                for candidate in result.get("candidates", [])
                if candidate.get("kind") == "pdf"
            ]
            status = "ok" if candidates else "no_candidates"

        print(f"DOI: {result.get('doi', doi)}")
        if result.get("is_oa") is not None:
            print(f"is_oa: {result['is_oa']}")
        if result.get("oa_status") is not None:
            print(f"oa_status: {result['oa_status']}")
        print(f"Status: {status}")
        print(f"Candidates: {len(candidates)}")
        for url in candidates[:5]:
            print(f"- {url['url']}")

        if status == "error":
            error = result.get("error")
            if error:
                print(f"Error: {error}")
            return 2

        if candidates:
            return 0
    return 0


def _write_unpaywall_report(lines: list[str]) -> Path:
    """Ecrit un rapport Unpaywall."""
    reports_dir = ensure_dir(reports_root())
    report_path = _unique_path(reports_dir / f"unpaywall_one_{_timestamp_tag()}.txt")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _run_unpaywall_fetch_one(doi: str | None) -> int:
    """Tente un download PDF via Unpaywall."""
    if not doi:
        print("ERREUR: --doi requis pour --unpaywall-fetch-one")
        return 2

    collection = choose_collection(collections_root())
    if collection is None:
        print("Aucune collection choisie.")
        return 0

    result = attempt_unpaywall_download(
        doi, collection, min_pdf_kb=UNPAYWALL_MIN_PDF_KB, log=print
    )
    result_label = "DOWNLOADED" if result["status"] == "downloaded" else "FAILED"
    reason_code = result["reason_code"]
    pdf_path = result["pdf_path"]
    candidates_total = result.get("candidates_total", 0)
    tried_count = result.get("tried_count", 0)
    error_message = result.get("error")

    print("")
    print("Resume")
    print(f"DOI: {doi}")
    print(f"Candidates total: {candidates_total}")
    print(f"Tried: {tried_count}")
    print(f"Result: {result_label}")
    print(f"Reason: {reason_code}")
    if pdf_path is not None:
        print(f"PDF: {pdf_path}")
    if error_message:
        print(f"Error: {error_message}")

    report_lines = [
        "Rapport Unpaywall fetch-one",
        f"DOI: {doi}",
        f"Candidates total: {candidates_total}",
        f"Tried: {tried_count}",
        f"Result: {result_label}",
        f"Reason: {reason_code}",
    ]
    if pdf_path is not None:
        report_lines.append(f"PDF: {pdf_path}")
    if error_message:
        report_lines.append(f"Error: {error_message}")

    report_path = _write_unpaywall_report(report_lines)
    print(f"Rapport: {report_path}")

    if reason_code == "ERROR":
        return 2
    return 0


def _run_unpaywall_run_csv(limit: int | None, verbose_progress: bool) -> int:
    """Execute un batch CSV Unpaywall."""
    try:
        collection = choose_collection(collections_root())
    except KeyboardInterrupt:
        print("Annulé")
        return 0
    if collection is None:
        print("Aucune collection choisie.")
        return 0

    try:
        csv_path = select_csv(Path.home() / "Desktop")
    except KeyboardInterrupt:
        print("Annulé")
        return 0
    if csv_path is None:
        if not was_cancelled_by_interrupt():
            print("Annulé")
        return 0

    return run_unpaywall_csv_batch(
        csv_path, collection, limit=limit, verbose_progress=verbose_progress
    )


def _run_uqar_proxy_export() -> int:
    """Exporte la proxy_queue UQAR."""
    bib_root = ensure_dir(bibliotheque_root())
    source = latest_to_be_downloaded(bib_root)
    if source is None:
        try:
            source = select_csv(Path.home() / "Desktop")
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if source is None:
            if not was_cancelled_by_interrupt():
                print("Annulé")
            return 0

    try:
        result = export_proxy_queue(source)
    except Exception as exc:
        print(f"Erreur export proxy_queue: {exc}")
        return 2
    print(f"Proxy queue: {result['proxy_queue_path']}")
    print(f"Rapport: {result['report_path']}")
    return 0


def _run_uqar_proxy_open() -> int:
    """Ouvre un lien UQAR depuis la proxy_queue."""
    bib_root = ensure_dir(bibliotheque_root())
    queue_path = latest_proxy_queue(bib_root)
    if queue_path is None:
        try:
            queue_path = select_csv(Path.home() / "Desktop")
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if queue_path is None:
            if not was_cancelled_by_interrupt():
                print("Annulé")
            return 0
    return open_proxy_queue(queue_path)


def _run_uqar_proxy_ingest() -> int:
    """Ingere les PDFs du proxy UQAR."""
    bib_root = ensure_dir(bibliotheque_root())
    proxy_queue_path = latest_proxy_queue(bib_root)
    if proxy_queue_path is None:
        try:
            proxy_queue_path = select_csv(Path.home() / "Desktop")
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if proxy_queue_path is None:
            if not was_cancelled_by_interrupt():
                print("Annulé")
            return 0

    run_csv_path = infer_run_csv_path(proxy_queue_path)
    if run_csv_path is None:
        try:
            run_csv_path = select_csv(Path.home() / "Desktop")
        except KeyboardInterrupt:
            print("Annulé")
            return 0
        if run_csv_path is None:
            if not was_cancelled_by_interrupt():
                print("Annulé")
            return 0

    try:
        proxy_queue_df = pd.read_csv(proxy_queue_path)
        run_df = pd.read_csv(run_csv_path)
    except Exception as exc:
        print(f"Erreur lecture CSV: {exc}")
        return 2

    collection = resolve_collection_for_ingest(proxy_queue_df, run_df)
    if collection is None:
        print("Annulé")
        return 0

    manual_import_dir = manual_import_dir_for_collection(collection)
    result = ingest_manual_pdfs(
        collection, manual_import_dir, proxy_queue_path, run_csv_path
    )
    if result.get("status") == "error":
        print(f"ERREUR: {result.get('message')}")
        return 2
    if result.get("status") == "empty":
        print(result.get("message"))
        return 0

    print("")
    print(f"Bibliotheque: {result['bibliotheque_path']}")
    print(f"A telecharger: {result['to_be_downloaded_path']}")
    print(f"Rapport: {result['report_path']}")
    print(f"Catalog diff: {result['catalog_diff']}")
    return 0


def _timestamp_tag() -> str:
    """Genere un horodatage pour les fichiers."""
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


def _run_demo_workflow(df: pd.DataFrame) -> None:
    """Execute le workflow demo."""
    ensure_dir(library_root())
    collections_dir = ensure_dir(collections_root())
    collection = choose_collection(collections_dir)
    if collection is None:
        print("Aucune collection choisie.")
        return

    bib_root = ensure_dir(bibliotheque_root())
    reports_dir = ensure_dir(reports_root())
    archives_dir = ensure_dir(archives_root())

    tag = _timestamp_tag()
    bibliotheque_path = _unique_path(bib_root / f"bibliotheque_{tag}.csv")
    to_be_downloaded_path = _unique_path(bib_root / f"to_be_downloaded_{tag}.csv")
    report_path = _unique_path(reports_dir / f"run_report_{tag}.txt")

    df.to_csv(bibliotheque_path, index=False)
    df.to_csv(to_be_downloaded_path, index=False)
    _archive_old_downloads(bib_root, archives_dir, to_be_downloaded_path)
    report_path = write_report(df, report_path)

    print(f"Bibliotheque: {bibliotheque_path}")
    print(f"A telecharger: {to_be_downloaded_path}")
    print(f"Rapport: {report_path}")


def _parse_args() -> argparse.Namespace:
    """Parse les arguments CLI."""
    parser = argparse.ArgumentParser(description="motherload_projet CLI")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Lance un workflow demo sans selection CSV.",
    )
    parser.add_argument(
        "--oa-smoke",
        action="store_true",
        help="Valide la config OA sans reseau.",
    )
    parser.add_argument(
        "--unpaywall-dry-run",
        action="store_true",
        help="Interroge Unpaywall et liste des URLs candidates.",
    )
    parser.add_argument(
        "--unpaywall-fetch-one",
        action="store_true",
        help="Tente un download via Unpaywall pour un DOI.",
    )
    parser.add_argument(
        "--unpaywall-demo-batch",
        action="store_true",
        help="Lance un batch Unpaywall de demo.",
    )
    parser.add_argument(
        "--unpaywall-run-csv",
        action="store_true",
        help="Lance un batch Unpaywall depuis un CSV.",
    )
    parser.add_argument(
        "--unpaywall-run-queue",
        action="store_true",
        help="Lance un batch Unpaywall depuis la queue.",
    )
    parser.add_argument(
        "--uqar-proxy-export",
        action="store_true",
        help="Exporte une proxy_queue UQAR depuis to_be_downloaded.",
    )
    parser.add_argument(
        "--uqar-proxy-open",
        action="store_true",
        help="Ouvre un lien UQAR depuis la proxy_queue.",
    )
    parser.add_argument(
        "--uqar-proxy-ingest",
        action="store_true",
        help="Ingere les PDFs du dossier manual_import.",
    )
    parser.add_argument(
        "--verbose-progress",
        action="store_true",
        help="Affiche une progression detaillee.",
    )
    parser.add_argument(
        "--make-sample-csv",
        action="store_true",
        help="Cree un CSV de demo sur le Desktop.",
    )
    parser.add_argument(
        "--doi",
        type=str,
        help="DOI a utiliser avec --unpaywall-dry-run ou --unpaywall-fetch-one.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limite le nombre de lignes pour --unpaywall-run-csv ou queue.",
    )
    return parser.parse_args()


def main() -> None:
    """Lance le CLI."""
    args = _parse_args()
    if args.make_sample_csv:
        raise SystemExit(_make_sample_csv())
    if args.oa_smoke:
        raise SystemExit(_run_oa_smoke())
    if args.uqar_proxy_export:
        raise SystemExit(_run_uqar_proxy_export())
    if args.uqar_proxy_open:
        raise SystemExit(_run_uqar_proxy_open())
    if args.uqar_proxy_ingest:
        raise SystemExit(_run_uqar_proxy_ingest())
    if args.unpaywall_fetch_one:
        raise SystemExit(_run_unpaywall_fetch_one(args.doi))
    if args.unpaywall_demo_batch:
        raise SystemExit(run_unpaywall_demo_batch(verbose_progress=args.verbose_progress))
    if args.unpaywall_run_csv:
        raise SystemExit(_run_unpaywall_run_csv(args.limit, args.verbose_progress))
    if args.unpaywall_run_queue:
        raise SystemExit(
            run_unpaywall_queue(
                limit=args.limit, verbose_progress=args.verbose_progress
            )
        )
    if args.unpaywall_dry_run:
        raise SystemExit(_run_unpaywall_dry_run(args.doi))

    print("motherload_projet MVP")

    if args.demo:
        demo_df = _demo_dataframe()
        _run_demo_workflow(demo_df)
        return

    selected = select_csv(Path.home() / "Desktop")
    if selected is not None:
        print(selected)


if __name__ == "__main__":
    main()
