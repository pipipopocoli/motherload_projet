#!/bin/bash
# Script de build pour Motherload
# Usage: ./build.sh

set -e

echo "🔨 Motherload Build Script"
echo "=========================="
echo ""

# Vérifier la venv
if [ ! -d ".venv" ]; then
    echo "❌ Erreur: .venv non trouvé"
    echo "Créez d'abord la venv: python3.11 -m venv .venv"
    exit 1
fi

# Activer venv
source .venv/bin/activate

# Vérifier PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installation de PyInstaller..."
    pip install --no-cache-dir pyinstaller
fi

# Nettoyer les anciens builds
echo "🧹 Nettoyage des anciens builds..."
rm -rf build/ dist/

# Build
echo "🚀 Lancement du build..."
pyinstaller motherload.spec

# Vérifier le résultat
if [ -d "dist/Motherload.app" ]; then
    echo ""
    echo "✅ Build réussi!"
    echo "📍 Application: dist/Motherload.app"
    echo ""
    echo "Pour lancer: open dist/Motherload.app"
else
    echo ""
    echo "❌ Build échoué"
    exit 1
fi
