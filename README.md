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

## Phase 2.6 (Unpaywall) - progress live + diagnostics

- Progression compacte par defaut (ligne unique + ETA).
- Option: `--verbose-progress` pour une ligne par item avec method.
- Colonnes ajoutees: is_oa, oa_status, url_for_pdf, last_http_status, tried_methods.

## Plan B UQAR Proxy (manuel assiste)

1) Run Unpaywall (CSV ou queue) pour generer un `to_be_downloaded_*.csv`
2) Exporter la proxy queue:

```bash
python -m motherload_projet.cli --uqar-proxy-export
```

3) Ouvrir un lien UQAR:

```bash
python -m motherload_projet.cli --uqar-proxy-open
```

4) Telecharger le PDF via le navigateur (acces institutionnel)
5) Deposer les PDFs dans:
   `~/Desktop/grand_librairy/pdfs/<collection>/manual_import/`
6) Ingerer les PDFs:

```bash
python -m motherload_projet.cli --uqar-proxy-ingest
```

Notes: pas d'automatisation de login/proxy, pas de bypass paywall.

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
