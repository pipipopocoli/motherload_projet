"""Fetch HTTP simple."""

from __future__ import annotations

import requests


def fetch_url(
    url: str, timeout: int = 30
) -> tuple[bool, int, str, str, bytes, str | None]:
    """Recupere une URL en HTTP."""
    headers = {"User-Agent": "motherload_projet/0.1"}
    try:
        response = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True
        )
    except requests.Timeout:
        return False, 0, "", url, b"", "TIMEOUT"
    except requests.RequestException:
        return False, 0, "", url, b"", "ERROR"

    content_type = response.headers.get("Content-Type", "")
    if ";" in content_type:
        content_type = content_type.split(";", 1)[0].strip()
    status_code = response.status_code
    ok = 200 <= status_code < 300
    return ok, status_code, content_type, response.url, response.content, None
