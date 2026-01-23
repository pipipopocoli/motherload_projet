# PROJECT_SPEC

MVP pour motherload_projet.

- Objectif: structure de base pour l ingestion, la bibliotheque, l interface et le reporting.
- Donnees locales: ~/Desktop/grand_librairy.
- Pas d acces reseau, pas d API, pas de telechargement.

## Structure data root

- ROOT: `~/Desktop/grand_librairy`
- COLLECTIONS_ROOT: `ROOT/collections`
- BIB_ROOT: `ROOT/bibliotheque`
- REPORTS_ROOT: `ROOT/reports`
- ARCHIVES: `BIB_ROOT/archives`

## Definitions

- Snapshot: fichier `bibliotheque_YYYYMMDD_HHMM.csv` dans `BIB_ROOT`.
- to_be_downloaded: fichier `to_be_downloaded_YYYYMMDD_HHMM.csv` dans `BIB_ROOT`,
  les anciens sont archives dans `ARCHIVES` (le plus recent reste accessible).

## Statut

- Phase 1 terminee (sans download).
