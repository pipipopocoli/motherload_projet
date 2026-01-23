"""Point d entree du CLI."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from motherload_projet.library.paths import (
    archives_root,
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
    reports_root,
)
from motherload_projet.reporting.summary import write_report
from motherload_projet.ui.collections_menu import choose_collection
from motherload_projet.ui.csv_navigator import navigate_csv


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
    return parser.parse_args()


def main() -> None:
    """Lance le CLI."""
    args = _parse_args()
    print("motherload_projet MVP")

    if args.demo:
        demo_df = _demo_dataframe()
        _run_demo_workflow(demo_df)
        return

    selected = navigate_csv()
    if selected is not None:
        print(selected)


if __name__ == "__main__":
    main()
