"""Fetch HTTP simple."""

from __future__ import annotations

import requests


from motherload_projet.data_mining.user_agents import get_random_header
from motherload_projet.data_mining.mining_logger import log_mining_error


def fetch_url(
    url: str, timeout: int = 30
) -> tuple[bool, int, str, str, bytes, str | None]:
    """Recupere une URL en HTTP avec rotation d'User-Agent et logging."""
    headers = get_random_header()
    try:
        response = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True
        )
    except requests.Timeout:
        log_mining_error(url, "TIMEOUT", "Request timed out")
        return False, 0, "", url, b"", "TIMEOUT"
    except requests.RequestException as e:
        log_mining_error(url, "CONNECTION_ERROR", str(e))
        return False, 0, "", url, b"", "ERROR"

    content_type = response.headers.get("Content-Type", "")
    if ";" in content_type:
        content_type = content_type.split(";", 1)[0].strip()
    status_code = response.status_code
    ok = 200 <= status_code < 300
    
    if not ok:
        log_mining_error(url, f"HTTP_{status_code}", "Non-200 status code", status_code)
        
    return ok, status_code, content_type, response.url, response.content, None
