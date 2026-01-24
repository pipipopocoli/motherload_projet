# motherload_projet — PROJECT_STATE (Phase 1)

## Commandes
- Activer venv: source .venv/bin/activate
- Lancer demo: python -m motherload_projet.cli --demo
- OA run CSV: python -m motherload_projet.cli --unpaywall-run-csv --limit 5
- Sample CSV: python -m motherload_projet.cli --make-sample-csv
- OA run queue: python -m motherload_projet.cli --unpaywall-run-queue
- Option: --verbose-progress (progress detaillee)

## Data library (sur Desktop)
ROOT: ~/Desktop/grand_librairy
- collections/            (collections + sous-collections)
- bibliotheque/           (fichiers de run)
  - archives/             (anciens to_be_downloaded_*)
- reports/                (rapports)
- pdfs/                   (PDFs plus tard)
- logs/                   (optionnel)
- game/                   (optionnel)

## Outputs par run (Phase 1)
- bibliotheque/bibliotheque_YYYYMMDD_HHMM.csv
- bibliotheque/to_be_downloaded_YYYYMMDD_HHMM.csv
- reports/run_report_YYYYMMDD_HHMM.txt
- bibliotheque/master_catalog.csv (sync)
Règle: archiver les anciens to_be_downloaded_* dans bibliotheque/archives (garder le plus récent accessible).

## Statut
Phase 1 validée: structure + demo + fichiers horodatés + archivage + report.
Phase 2.4: navigateur CSV + annulation propre + sample csv.
Phase 2.5: progression + master catalog + queue runner.
Phase 2.6: progress verbose + ETA glissante.
