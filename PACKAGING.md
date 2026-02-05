# Packaging Guide - Motherload

## Installation de PyInstaller

### Méthode Standard
```bash
source .venv/bin/activate
pip install pyinstaller
```

### Si erreurs de permissions (cache Python 3.9)
```bash
# Nettoyer les anciens fichiers
find .venv/lib/python3.11/site-packages -name "*.cpython-39.pyc" -delete
find .venv/lib/python3.11/site-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Réinstaller
pip install --force-reinstall --no-cache-dir pyinstaller
```

### Alternative: Nouvelle venv
```bash
# Si le problème persiste, recréer la venv
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Build de l'application

```bash
pyinstaller motherload.spec
```

Cela créera:
- `dist/Motherload.app` (macOS) - Application standalone
- `build/` - Fichiers temporaires de build

## Lancement de l'app packagée

```bash
open dist/Motherload.app
```

## Notes

- Le fichier `motherload.spec` contient la configuration PyInstaller
- Les dépendances cachées (tkinterdnd2, pandas) sont déjà configurées
- Les fichiers de données (agents_manuals, catalogs) sont inclus automatiquement
- L'app est configurée en mode "windowed" (pas de console)

## Troubleshooting

Si l'app ne démarre pas:
1. Vérifier les logs dans Console.app (macOS)
2. Tester d'abord avec `console=True` dans le .spec
3. Vérifier que toutes les dépendances sont dans requirements.txt
4. Tester l'app sans build: `python -m motherload_projet.desktop_app.app`
