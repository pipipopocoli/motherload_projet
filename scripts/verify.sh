#!/usr/bin/env bash
set -euo pipefail

ruff check app motherload_projet tests
pytest
