# AGENTS

Ce fichier decrit les regles locales pour les agents.

# AGENTS.md — motherload_projet

## Objectif du repo
Construire un outil Python pour:
- Lire un CSV de métadonnées (articles/livres)
- Télécharger des PDFs (Open Access d’abord)
- Maintenir une bibliothèque locale sur Desktop: ~/Desktop/grand_librairy
- Produire des snapshots horodatés + rapports + liste "to_be_downloaded"

## Contrainte critique
- Ne jamais écrire de PDFs dans le repo Git.
- Tous les PDFs vont dans: ~/Desktop/grand_librairy/pdfs/<collection>/
- Les outputs run vont dans:
  - ~/Desktop/grand_librairy/bibliotheque/
  - ~/Desktop/grand_librairy/reports/

## Philosophie de dev
- Changements minimaux: ne pas refactoriser ce qui marche.
- Préférer petits modules clairs plutôt qu’un gros fichier.
- Docstrings courtes en français.
- Ajouter/mettre à jour README.md, PROJECT_STATE.md, LOGBOOK.md quand on ajoute une feature CLI.

## Commandes de base
- venv: source .venv/bin/activate
- help CLI: python -m motherload_projet.cli -h
- Demo Phase 1: python -m motherload_projet.cli --demo
- OA fetch one: python -m motherload_projet.cli --unpaywall-fetch-one --doi <DOI>
- OA demo batch: python -m motherload_projet.cli --unpaywall-demo-batch
- OA run CSV: python -m motherload_projet.cli --unpaywall-run-csv --limit 5

## Style / Qualité
- Logs lisibles, erreurs expliquées en 1 ligne.
- Toujours retourner un reason_code clair (OK, NO_PDF_FOUND, MISSING_DOI, TIMEOUT, HTTP_403, HTTP_429, ERROR).
- Gérer proprement l’annulation utilisateur (q, Ctrl+C): pas de stacktrace, message "Annulé".

