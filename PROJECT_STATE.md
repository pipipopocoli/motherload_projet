# motherload_projet — PROJECT_STATE (Phase 1)

## Commandes
- Activer venv: source .venv/bin/activate
- Lancer demo: python -m motherload_projet.cli --demo
- OA run CSV: python -m motherload_projet.cli --unpaywall-run-csv --limit 5
- Sample CSV: python -m motherload_projet.cli --make-sample-csv
- OA run queue: python -m motherload_projet.cli --unpaywall-run-queue
- UQAR proxy export: python -m motherload_projet.cli --uqar-proxy-export
- UQAR proxy open: python -m motherload_projet.cli --uqar-proxy-open (ouvre le prochain lien)
- UQAR proxy ingest: python -m motherload_projet.cli --uqar-proxy-ingest
- Manual ingest UI: python -m motherload_projet.cli --manual-ingest-ui
- Manual ingest one: python -m motherload_projet.cli --manual-ingest-one --pdf /chemin/vers/fichier.pdf
- Option: --verbose-progress (progress detaillee)
Note: UQAR_EZPROXY_PREFIX requis pour generer les liens proxy.

## Data library (sur Desktop)
ROOT: ~/Desktop/grand_librairy
- collections/            (collections + sous-collections)
- bibliotheque/           (fichiers de run)
  - archives/             (anciens to_be_downloaded_*)
- reports/                (rapports)
- pdfs/                   (PDFs + import manuel dans pdfs/<collection>/<MANUAL_IMPORT_SUBDIR>/)
- logs/                   (optionnel)
- game/                   (optionnel)

## Outputs par run (Phase 1)
- bibliotheque/bibliotheque_YYYYMMDD_HHMM.csv
- bibliotheque/to_be_downloaded_YYYYMMDD_HHMM.csv
- bibliotheque/proxy_queue_YYYYMMDD_HHMM.csv
- reports/run_report_YYYYMMDD_HHMM.txt
- reports/proxy_queue_report_YYYYMMDD_HHMM.txt
- reports/ingest_report_YYYYMMDD_HHMM.txt
- reports/manual_ingest_YYYYMMDD_HHMM.txt
- bibliotheque/master_catalog.csv (sync)
Règle: archiver les anciens to_be_downloaded_* dans bibliotheque/archives (garder le plus récent accessible).

## Statut
Phase 1 validée: structure + demo + fichiers horodatés + archivage + report.
Phase 2.4: navigateur CSV + annulation propre + sample csv.
Phase 2.5: progression + master catalog + queue runner.
Phase 2.6: progress live + ETA glissante + diagnostics OA/HTTP.
Phase 2.7: proxy UQAR (export/open/ingest) + liens EZproxy + import manuel PDFs.
Phase 2.x: ingestion manuelle PDF (UI Tkinter + CLI one) + dedupe hash + update master_catalog.
Phase 2.y: ecosysteme visuel (organigramme modules/fonctions + notes + auto update watchdog + deps).
Phase 2.z: reorganisation dossiers (data_mining, local_pdf_update, rapport_activite, maintenance_manager, connecteurs).
