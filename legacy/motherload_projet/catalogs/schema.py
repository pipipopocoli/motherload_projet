"""Schemas simples pour catalogues et scans."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScanConfig:
    """Configuration du scan."""

    enable_grobid: bool = False
    grobid_url: str | None = None
    enable_ocr: bool = True
    ocr_lang: str = "eng"
    crossref_mailto: str | None = None
    semantic_fields: str = "title,year,authors,venue,journal,volume,issue,pages"
    rate_limit_sec: float = 0.3
    cache_path: Path | None = None
    max_pages_text: int = 2
    max_pages_doi: int = 0
    max_pages_ocr: int = 2
    max_workers: int = 8


@dataclass
class ScanRunSummary:
    """Resume d'un scan."""

    timestamp: str
    total_pdfs: int
    processed_pdfs: int
    created: int
    updated: int
    matched: int
    errors: int
    warnings: int
    error_counts: dict[str, int] = field(default_factory=dict)
    warning_counts: dict[str, int] = field(default_factory=dict)
    reports: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit en dict."""
        return {
            "timestamp": self.timestamp,
            "total_pdfs": self.total_pdfs,
            "processed_pdfs": self.processed_pdfs,
            "created": self.created,
            "updated": self.updated,
            "matched": self.matched,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_counts": dict(self.error_counts),
            "warning_counts": dict(self.warning_counts),
            "reports": dict(self.reports),
            "outputs": dict(self.outputs),
            "extra": dict(self.extra),
        }
