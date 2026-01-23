"""Navigation CSV pour le MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys


@dataclass(frozen=True)
class Entry:
    """Entree de navigation."""

    kind: str
    path: Path


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


def _copy_to_clipboard(text: str) -> bool:
    """Copie du texte dans le presse papier si possible."""
    if sys.platform.startswith("darwin"):
        cmd = ["pbcopy"]
    elif sys.platform.startswith("win"):
        cmd = ["clip"]
    else:
        cmd = ["xclip", "-selection", "clipboard"]

    if shutil.which(cmd[0]) is None:
        return False

    try:
        subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def navigate_csv(start_dir: Path | str | None = None) -> str | None:
    """Navigue pour choisir un fichier CSV."""
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
            label = "D" if entry.kind == "dir" else "CSV"
            print(f"{index}) [{label}] {entry.path.name}")

        print(
            "Commandes: 0=remonter, numero=entrer/selectionner, "
            "s=filtrer, p=coller chemin, q=quit"
        )

        choice = input("> ").strip()
        if not choice:
            continue

        lowered = choice.lower()
        if lowered == "q":
            return None
        if lowered == "s":
            filter_text = input("Filtre: ").strip()
            continue
        if lowered == "p":
            path_text = str(current)
            if _copy_to_clipboard(path_text):
                print("Chemin copie dans le presse papier.")
            else:
                print(path_text)
            continue

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

            return str(entry.path.resolve())

        print("Commande inconnue.")
