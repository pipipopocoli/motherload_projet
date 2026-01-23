# MANUAL — motherload_projet (Phase 1)

## But
Phase 1 = infrastructure: collections, runs horodatés, snapshots, rapports. Aucun téléchargement.

## CLI (définition)
CLI = interface terminal (ex: `python -m motherload_projet.cli --demo`) qui orchestre le programme.

## Data library (source de vérité)
ROOT: ~/Desktop/grand_librairy
- collections/
- bibliotheque/
  - archives/
- reports/
- pdfs/
- logs/
- game/

## Commandes
Activation venv:
- source .venv/bin/activate

Démo:
- python -m motherload_projet.cli --demo

## Outputs par run
- bibliotheque/bibliotheque_YYYYMMDD_HHMM.csv
- bibliotheque/to_be_downloaded_YYYYMMDD_HHMM.csv
- reports/run_report_YYYYMMDD_HHMM.txt

Règle archives: anciens to_be_downloaded_* -> bibliotheque/archives (le plus récent reste accessible).

## Vérifications
- python -m compileall motherload_projet -q
- python -m motherload_projet.cli --demo
- ls -lt ~/Desktop/grand_librairy/bibliotheque | head -n 10
- ls -lt ~/Desktop/grand_librairy/reports | head -n 10
