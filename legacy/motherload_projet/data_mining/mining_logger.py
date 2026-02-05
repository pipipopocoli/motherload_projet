"""
Module pour la gestion centralisée des logs d'erreurs de mining.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configuration du fichier de log à la racine du projet (ou ailleurs si besoin)
# On va le mettre à la racine du workspace pour qu'il soit visible.
LOG_FILE_PATH = Path("mining_errors.log").resolve()

def _setup_logger():
    logger = logging.getLogger("mining_errors")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        
        # File Handler
        fh = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
        fh.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
    return logger

_logger = _setup_logger()

def log_mining_error(url: str, error_type: str, details: str, status_code: Optional[int] = None):
    """
    Logue une erreur de mining dans le fichier centralisé.
    
    Args:
        url: L'URL qui a causé l'erreur.
        error_type: Le type d'erreur (ex: 'TIMEOUT', 'HTTP_403', 'INVALID_PDF').
        details: Détails supplémentaires ou message d'exception.
        status_code: Code HTTP si applicable.
    """
    status_str = f" [Status: {status_code}]" if status_code else ""
    message = f"URL: {url} | Type: {error_type}{status_str} | Details: {details}"
    _logger.error(message)

def get_log_path() -> Path:
    return LOG_FILE_PATH
