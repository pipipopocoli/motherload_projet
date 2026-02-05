"""Gestion de la configuration."""

from __future__ import annotations

import os

# On tente de charger dotenv, mais on ignore silencieusement les erreurs de permission
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _read_env(key: str) -> str | None:
    """Lit une variable d environnement."""
    value = os.getenv(key)
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return value


def get_unpaywall_email() -> str | None:
    """Retourne l email Unpaywall."""
    val = _read_env("UNPAYWALL_EMAIL")
    if val:
        return val
    return "olivier.cloutier.dev@gmail.com"


def get_openalex_key() -> str | None:
    """Retourne la cle OpenAlex."""
    return _read_env("OPENALEX_API_KEY")


def get_uqar_ezproxy_prefix() -> str | None:
    """Retourne le prefix UQAR EZproxy."""
    return _read_env("UQAR_EZPROXY_PREFIX")


def get_manual_import_subdir() -> str:
    """Retourne le sous-dossier d import manuel."""
    value = _read_env("MANUAL_IMPORT_SUBDIR")
    if not value:
        return "manual_import"
    return value


def get_crossref_email() -> str | None:
    """Retourne l email pour Crossref."""
    return _read_env("CROSSREF_EMAIL")
