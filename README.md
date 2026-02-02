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

1) Configurer `.env`:
   - `UQAR_EZPROXY_PREFIX` (necessaire pour generer les liens)
   - `MANUAL_IMPORT_SUBDIR` (optionnel, defaut: manual_import)
2) Run Unpaywall (CSV ou queue) pour generer un `to_be_downloaded_*.csv`
3) Exporter la proxy queue:

```bash
python -m motherload_projet.cli --uqar-proxy-export
```

4) Ouvrir le premier lien UQAR restant:

```bash
python -m motherload_projet.cli --uqar-proxy-open
```

Relancer la commande pour ouvrir le lien suivant.

5) Telecharger le PDF via le navigateur (acces institutionnel)
6) Deposer les PDFs dans:
   `~/Desktop/grand_librairy/pdfs/<collection>/<MANUAL_IMPORT_SUBDIR>/`
7) Ingerer les PDFs:

```bash
python -m motherload_projet.cli --uqar-proxy-ingest
```

Notes: pas d'automatisation de login/proxy, pas de bypass paywall.

## Phase 2.x (Ingestion manuelle PDF - local)

UI Tkinter:

```bash
python -m motherload_projet.cli --manual-ingest-ui
```

Ingestion directe (1 fichier):

```bash
python -m motherload_projet.cli --manual-ingest-one --pdf /chemin/vers/fichier.pdf
```

Le PDF est deplace vers:
`~/Desktop/grand_librairy/pdfs/<collection>/<MANUAL_IMPORT_SUBDIR>/`

Le `master_catalog.csv` est mis a jour (file_hash/source/added_at) et un
report est genere dans `~/Desktop/grand_librairy/reports/`.

## Phase 2.y (Ecosysteme - visualisation code)

- Onglet \"Ecosysteme\" dans l UI.
- Organigramme des modules/fonctions (tree interactif).
- Double-clic sur une fonction pour voir le detail et prendre des notes.
- Notes sauvegardees dans des fichiers texte locaux.
- Auto update du schema avec watchdog (si actif).
- Mini outil pour verifier/mettre a jour les dependances.

## Emplacements des fichiers

- Racine des donnees: `~/Desktop/grand_librairy`
- Collections: `~/Desktop/grand_librairy/collections`
- Bibliotheque: `~/Desktop/grand_librairy/bibliotheque`
  - `bibliotheque_YYYYMMDD_HHMM.csv`
  - `to_be_downloaded_YYYYMMDD_HHMM.csv`
  - `proxy_queue_YYYYMMDD_HHMM.csv`
  - `master_catalog.csv`
  - Archives: `~/Desktop/grand_librairy/bibliotheque/archives`
- Rapports: `~/Desktop/grand_librairy/reports`
  - `run_report_YYYYMMDD_HHMM.txt`
  - `catalog_diff_YYYYMMDD_HHMM.txt`
  - `proxy_queue_report_YYYYMMDD_HHMM.txt`
  - `ingest_report_YYYYMMDD_HHMM.txt`
  - `manual_ingest_YYYYMMDD_HHMM.txt`
- Ecosysteme:
  - `~/Desktop/grand_librairy/ecosysteme_visualisation/index.json`
  - `~/Desktop/grand_librairy/ecosysteme_visualisation/notes/*.txt`

## Test manuel (ingestion PDF)

1) Creer un faux PDF minimal (ou utiliser un PDF existant).
2) Lancer `--manual-ingest-one` sur ce fichier.
3) Verifier le deplacement dans `grand_librairy/pdfs/<collection>/<subdir>/`.
4) Verifier que `master_catalog.csv` contient `file_hash` et `pdf_path`.
