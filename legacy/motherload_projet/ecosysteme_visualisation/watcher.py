"""Surveillance du code avec watchdog."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[], None], debounce_s: float = 0.6) -> None:
        super().__init__()
        self._on_change = on_change
        self._debounce_s = debounce_s
        self._timer: threading.Timer | None = None

    def on_any_event(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        if not str(event.src_path).endswith(".py"):
            return
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self._debounce_s, self._on_change)
        self._timer.daemon = True
        self._timer.start()


def start_watchdog(code_root: Path, on_change: Callable[[], None]) -> Observer:
    """Demarre le watchdog sur un dossier."""
    handler = _DebouncedHandler(on_change)
    observer = Observer()
    observer.schedule(handler, str(code_root), recursive=True)
    observer.daemon = True
    observer.start()
    return observer
