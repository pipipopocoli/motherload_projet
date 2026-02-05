"""Chemins de la bibliotheque."""

from __future__ import annotations

from pathlib import Path

ROOT = Path.home() / "Desktop" / "grand_librairy"
COLLECTIONS_ROOT = ROOT / "collections"
BIB_ROOT = ROOT / "bibliotheque"
REPORTS_ROOT = ROOT / "reports"
ARCHIVES = BIB_ROOT / "archives"


def library_root() -> Path:
    """Retourne la racine de donnees locale."""
    return ROOT


def collections_root() -> Path:
    """Retourne la racine des collections."""
    return COLLECTIONS_ROOT


def bibliotheque_root() -> Path:
    """Retourne la racine bibliotheque."""
    return BIB_ROOT


def reports_root() -> Path:
    """Retourne la racine des rapports."""
    return REPORTS_ROOT


def archives_root() -> Path:
    """Retourne la racine des archives."""
    return ARCHIVES


def ensure_dir(path: Path) -> Path:
    """Cree le dossier si besoin."""
    path.mkdir(parents=True, exist_ok=True)
    return path
