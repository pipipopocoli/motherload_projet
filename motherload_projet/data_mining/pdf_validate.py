"""Validation PDF."""

from __future__ import annotations


def is_pdf_bytes(content: bytes) -> bool:
    """Verifie la signature PDF."""
    return content.startswith(b"%PDF")


def validate_pdf_bytes(content: bytes, min_size_kb: int = 100) -> tuple[bool, str]:
    """Valide un PDF par bytes."""
    if not content:
        return False, "EMPTY"
    if not is_pdf_bytes(content):
        return False, "NOT_PDF"
    if len(content) < min_size_kb * 1024:
        return False, "TOO_SMALL"
    return True, "OK"
