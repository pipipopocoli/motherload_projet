"""Etat local de l app desktop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motherload_projet.library.paths import ensure_dir, library_root

STATE_FILENAME = "app_state.json"

DEFAULT_PHASES = [
    {"id": "phase1", "label": "Phase 1 (structure)", "weight": 15},
    {"id": "phase2", "label": "Phase 2 (Unpaywall)", "weight": 25},
    {"id": "phase27", "label": "Phase 2.7 (proxy UQAR)", "weight": 15},
    {"id": "phase2x", "label": "Phase 2.x (ingest manuel)", "weight": 15},
    {"id": "phase3", "label": "Phase 3 (dashboard/recherche)", "weight": 20},
    {"id": "phase4", "label": "Phase 4 (Obsidian/ChatGPT)", "weight": 10},
]

DEFAULT_TASKS = [
    {
        "id": "p1_structure",
        "label": "Structure data root + demo",
        "phase": "phase1",
        "priority": 1,
        "done": True,
    },
    {
        "id": "p2_unpaywall",
        "label": "Unpaywall CSV + queue + catalog",
        "phase": "phase2",
        "priority": 1,
        "done": True,
    },
    {
        "id": "p27_proxy",
        "label": "Proxy UQAR + ingest manuel",
        "phase": "phase27",
        "priority": 1,
        "done": True,
    },
    {
        "id": "p2x_manual_ui",
        "label": "UI ingest manuel (local)",
        "phase": "phase2x",
        "priority": 1,
        "done": True,
    },
    {
        "id": "p3_recherche",
        "label": "Recherche + ouverture PDF",
        "phase": "phase3",
        "priority": 1,
        "done": False,
    },
    {
        "id": "p3_dashboard",
        "label": "Dashboard compteurs",
        "phase": "phase3",
        "priority": 1,
        "done": False,
    },
    {
        "id": "p3_checklist",
        "label": "Checklist prioritaire",
        "phase": "phase3",
        "priority": 2,
        "done": False,
    },
    {
        "id": "p4_obsidian",
        "label": "Integration Obsidian",
        "phase": "phase4",
        "priority": 2,
        "done": False,
    },
    {
        "id": "p4_chatgpt",
        "label": "Integration ChatGPT",
        "phase": "phase4",
        "priority": 3,
        "done": False,
    },
]


def _state_path() -> Path:
    """Retourne le chemin de l etat."""
    root = ensure_dir(library_root())
    return root / STATE_FILENAME


def default_state() -> dict[str, Any]:
    """Construit l etat par defaut."""
    return {
        "phases": DEFAULT_PHASES,
        "tasks": DEFAULT_TASKS,
    }


def _merge_state(base: dict[str, Any], saved: dict[str, Any]) -> dict[str, Any]:
    """Fusionne un etat sauvegarde."""
    phases = {item["id"]: item for item in base.get("phases", [])}
    for item in saved.get("phases", []):
        if "id" in item:
            phases[item["id"]] = {**phases.get(item["id"], {}), **item}

    tasks = {item["id"]: item for item in base.get("tasks", [])}
    for item in saved.get("tasks", []):
        if "id" in item:
            tasks[item["id"]] = {**tasks.get(item["id"], {}), **item}

    return {
        "phases": list(phases.values()),
        "tasks": list(tasks.values()),
    }


def load_state() -> dict[str, Any]:
    """Charge l etat local."""
    path = _state_path()
    base = default_state()
    if not path.exists():
        save_state(base)
        return base
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        save_state(base)
        return base
    merged = _merge_state(base, raw)
    save_state(merged)
    return merged


def save_state(state: dict[str, Any]) -> None:
    """Sauvegarde l etat local."""
    path = _state_path()
    try:
        path.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except OSError:
        return


def reset_tasks() -> dict[str, Any]:
    """Reinitialise la checklist."""
    state = default_state()
    save_state(state)
    return state


def compute_progress(state: dict[str, Any]) -> dict[str, Any]:
    """Calcule la progression."""
    phases = state.get("phases", [])
    tasks = state.get("tasks", [])
    tasks_by_phase: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        phase = task.get("phase", "")
        tasks_by_phase.setdefault(phase, []).append(task)

    total_weight = sum(float(item.get("weight", 0)) for item in phases) or 1.0
    weighted_done = 0.0
    per_phase: dict[str, float] = {}
    for phase in phases:
        phase_id = phase.get("id", "")
        phase_weight = float(phase.get("weight", 0))
        phase_tasks = tasks_by_phase.get(phase_id, [])
        if not phase_tasks:
            ratio = 0.0
        else:
            done = sum(1 for task in phase_tasks if task.get("done"))
            ratio = done / max(len(phase_tasks), 1)
        per_phase[phase_id] = ratio
        weighted_done += ratio * phase_weight

    percent = max(0.0, min(100.0, (weighted_done / total_weight) * 100.0))
    return {
        "percent": percent,
        "per_phase": per_phase,
    }
