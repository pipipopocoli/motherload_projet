# motherload_projet

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Lancer la demo

```bash
python -m motherload_projet.cli --demo
```

## Phase 2 (OA) - smoke test

```bash
python -m motherload_projet.cli --oa-smoke
```

## Phase 2.1 (Unpaywall) - dry run

```bash
python -m motherload_projet.cli --unpaywall-dry-run
```

Ne telecharge pas, affiche seulement les URLs candidates.

## Phase 2.4 (Unpaywall) - CSV

```bash
python -m motherload_projet.cli --unpaywall-run-csv --limit 5
```

```bash
python -m motherload_projet.cli --make-sample-csv
```

## Phase 2.5 (Unpaywall) - queue + catalog

```bash
python -m motherload_projet.cli --unpaywall-run-queue
```

Option: ajouter `--verbose-progress` pour un affichage detaille.

## Emplacements des fichiers

- Racine des donnees: `~/Desktop/grand_librairy`
- Collections: `~/Desktop/grand_librairy/collections`
- Bibliotheque: `~/Desktop/grand_librairy/bibliotheque`
  - `bibliotheque_YYYYMMDD_HHMM.csv`
  - `to_be_downloaded_YYYYMMDD_HHMM.csv`
  - `master_catalog.csv`
  - Archives: `~/Desktop/grand_librairy/bibliotheque/archives`
- Rapports: `~/Desktop/grand_librairy/reports`
  - `run_report_YYYYMMDD_HHMM.txt`
  - `catalog_diff_YYYYMMDD_HHMM.txt`
