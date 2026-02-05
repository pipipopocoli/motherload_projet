#!/usr/bin/env python3
"""Benchmark PDF parsing against a golden corpus."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from pypdf import PdfReader


@dataclass
class BenchmarkResult:
    filename: str
    pages: int
    elapsed_sec: float
    time_per_page_sec: float | None
    word_count: int
    status: str
    error: str | None = None


def _count_words(text: str) -> int:
    return len(text.split()) if text else 0


def benchmark_pdf(path: Path) -> BenchmarkResult:
    start_total = perf_counter()
    page_times: list[float] = []
    word_count = 0
    status = "OK"
    error: str | None = None

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            status = "ENCRYPTED"
        pages = len(reader.pages)
        for page in reader.pages:
            start_page = perf_counter()
            text = page.extract_text() or ""
            page_times.append(perf_counter() - start_page)
            word_count += _count_words(text)
    except Exception as exc:  # pylint: disable=broad-except
        status = "ERROR"
        error = f"{type(exc).__name__}: {exc}"
        pages = 0

    elapsed = perf_counter() - start_total
    time_per_page = None
    if page_times:
        time_per_page = sum(page_times) / len(page_times)
    elif pages > 0:
        time_per_page = elapsed / pages

    if status == "OK" and word_count == 0:
        status = "EMPTY_TEXT"

    return BenchmarkResult(
        filename=path.name,
        pages=pages,
        elapsed_sec=round(elapsed, 4),
        time_per_page_sec=round(time_per_page, 6) if time_per_page else None,
        word_count=word_count,
        status=status,
        error=error,
    )


def benchmark_corpus(corpus_dir: Path) -> list[BenchmarkResult]:
    pdf_files = sorted(corpus_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {corpus_dir}")
    return [benchmark_pdf(path) for path in pdf_files]


def build_report(results: list[BenchmarkResult], corpus_dir: Path) -> dict[str, Any]:
    total = len(results)
    ok = sum(1 for r in results if r.status == "OK")
    empty = sum(1 for r in results if r.status == "EMPTY_TEXT")
    errors = sum(1 for r in results if r.status == "ERROR")
    encrypted = sum(1 for r in results if r.status == "ENCRYPTED")

    return {
        "corpus": str(corpus_dir),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total,
            "ok": ok,
            "empty_text": empty,
            "errors": errors,
            "encrypted": encrypted,
        },
        "results": [r.__dict__ for r in results],
    }


def write_report(report: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return output_path


def run_benchmark(corpus_dir: Path, output_path: Path | None = None) -> Path:
    results = benchmark_corpus(corpus_dir)
    report = build_report(results, corpus_dir)
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("outputs") / f"parsing_benchmark_{timestamp}.json"
    return write_report(report, output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark PDF parsing")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("inputs/golden_corpus"),
        help="Directory containing PDF fixtures",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path",
    )

    args = parser.parse_args()
    if not args.corpus.exists():
        print(f"Error: Corpus directory {args.corpus} not found.")
        return 1

    report_path = run_benchmark(args.corpus, args.output)
    print(f"Benchmark report written to: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
