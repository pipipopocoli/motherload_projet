# Motherload

Desktop app locale (macOS), single-user. Stack principale: `app/` (Qt/PySide6 + SQLAlchemy).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Lancer l'app (Qt)

```bash
python -m app.main
```

## CLI (app)

```bash
python -m app.cli --help
```

## Legacy (gelé)

L'ancien pipeline Tkinter/CLI est déplacé dans `legacy/` et n'est plus maintenu.
Voir `legacy/README.md` pour référence.
