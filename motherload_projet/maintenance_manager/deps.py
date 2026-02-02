"""Gestion simple des dependances."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable


def list_outdated() -> list[dict[str, Any]]:
    """Liste les paquets obsoletes."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def upgrade_requirements(requirements_path: Path) -> tuple[int, str]:
    """Met a jour les dependances du requirements."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-r",
                str(requirements_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return 1, f"Erreur: {exc}"
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    return result.returncode, output.strip()


def start_auto_update(
    requirements_path: Path,
    interval_minutes: int,
    on_log: Callable[[str], None] | None = None,
) -> threading.Event:
    """Demarre un update auto a intervalle fixe."""
    stop_event = threading.Event()

    def _loop() -> None:
        while not stop_event.is_set():
            code, output = upgrade_requirements(requirements_path)
            if on_log:
                status = "OK" if code == 0 else "ERROR"
                on_log(f"Auto update deps -> {status}")
                if output:
                    on_log(output)
            stop_event.wait(max(60, interval_minutes * 60))

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return stop_event
