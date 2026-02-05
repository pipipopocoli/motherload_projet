#!/usr/bin/env python3
"""
Test script for dry-run mode of retro_clean_library.
"""

from pathlib import Path
from motherload_projet.local_pdf_update.local_pdf import retro_clean_library
from motherload_projet.library.paths import library_root

# Test on a specific small collection or create a test directory
test_root = library_root() / "pdfs"

print("=" * 60)
print("TESTING DRY-RUN MODE")
print("=" * 60)
print(f"Test root: {test_root}")
print()

# Run dry-run
print("Running DRY-RUN mode...")
result = retro_clean_library(pdf_root=test_root, dry_run=True)

print()
print("=" * 60)
print("DRY-RUN RESULTS")
print("=" * 60)
print(f"Total files scanned: {result['total']}")
print(f"Files that would be updated: {result['updated']}")
print(f"Catalog entries that would be created: {result['created']}")
print(f"Errors: {result['errors']}")
print(f"Suggestions: {result['suggestions']}")
print(f"Report path: {result['report_path']}")
print()

# Display first 50 lines of the report
if result['report_path']:
    report_path = Path(result['report_path'])
    if report_path.exists():
        print("=" * 60)
        print("REPORT PREVIEW (first 50 lines)")
        print("=" * 60)
        lines = report_path.read_text(encoding='utf-8').splitlines()
        for line in lines[:50]:
            print(line)
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")
