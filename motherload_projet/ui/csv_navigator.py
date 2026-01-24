"""Navigation CSV pour le MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    """Entree de navigation."""

    kind: str
    path: Path


_LAST_CANCELLED_BY_INTERRUPT = False


def _list_entries(current: Path, filter_text: str | None) -> list[Entry]:
    """Liste dossiers et CSVs avec filtrage optionnel."""
    entries: list[Entry] = []
    for item in current.iterdir():
        if item.is_dir():
            entries.append(Entry(kind="dir", path=item))
        elif item.is_file() and item.suffix.lower() == ".csv":
            entries.append(Entry(kind="csv", path=item))

    entries.sort(key=lambda entry: (entry.kind != "dir", entry.path.name.lower()))
    if filter_text:
        lowered = filter_text.lower()
        entries = [entry for entry in entries if lowered in entry.path.name.lower()]
    return entries


def _read_input(prompt: str) -> str | None:
    """Lit une entree utilisateur."""
    global _LAST_CANCELLED_BY_INTERRUPT
    try:
        return input(prompt)
    except KeyboardInterrupt:
        _LAST_CANCELLED_BY_INTERRUPT = True
        print("Annulé")
        return None


def _resolve_pasted_path(value: str) -> Path | None:
    """Valide un chemin colle."""
    cleaned = value.strip().strip("'").strip('"')
    if not cleaned:
        return None
    candidate = Path(cleaned).expanduser()
    if not candidate.is_absolute():
        return None
    if not candidate.is_file():
        return None
    if candidate.suffix.lower() != ".csv":
        return None
    return candidate.resolve()


def select_csv(start_dir: Path | str | None = None) -> Path | None:
    """Selectionne un fichier CSV."""
    global _LAST_CANCELLED_BY_INTERRUPT
    _LAST_CANCELLED_BY_INTERRUPT = False
    if start_dir is None:
        start_dir = Path.home() / "Desktop"

    current = Path(start_dir).expanduser()
    if not current.exists():
        current = Path.home()

    filter_text = ""
    while True:
        entries = _list_entries(current, filter_text or None)
        print("")
        print(f"Dossier: {current}")
        if filter_text:
            print(f"Filtre: {filter_text}")
        print("0) ..")
        for index, entry in enumerate(entries, start=1):
            label = "D" if entry.kind == "dir" else "F"
            print(f"{index}) [{label}] {entry.path.name}")

        print(
            "Commandes: 0=remonter, numero=entrer/selectionner, "
            "s=filtrer, p=coller chemin, q=quit"
        )

        choice = _read_input("> ")
        if choice is None:
            return None
        choice = choice.strip()
        if not choice:
            continue

        lowered = choice.lower()
        if lowered == "q":
            _LAST_CANCELLED_BY_INTERRUPT = False
            return None
        if lowered == "s":
            value = _read_input("Filtre: ")
            if value is None:
                return None
            filter_text = value.strip()
            continue
        if lowered == "p":
            value = _read_input("Chemin: ")
            if value is None:
                return None
            path = _resolve_pasted_path(value)
            if path is None:
                print("Chemin invalide.")
                continue
            return path

        if choice.isdigit():
            index = int(choice)
            if index == 0:
                parent = current.parent
                if parent != current:
                    current = parent
                continue

            entry_index = index - 1
            if entry_index < 0 or entry_index >= len(entries):
                print("Choix invalide.")
                continue

            entry = entries[entry_index]
            if entry.kind == "dir":
                current = entry.path
                continue

            _LAST_CANCELLED_BY_INTERRUPT = False
            return entry.path.resolve()

        print("Commande inconnue.")


def was_cancelled_by_interrupt() -> bool:
    """Indique une annulation par Ctrl+C."""
    return _LAST_CANCELLED_BY_INTERRUPT


def navigate_csv(start_dir: Path | str | None = None) -> str | None:
    """Compatibilite pour navigation CSV."""
    selected = select_csv(start_dir)
    if selected is None:
        return None
    return str(selected)
