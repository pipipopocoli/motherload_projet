"""Menu des collections pour le MVP."""

from __future__ import annotations

from pathlib import Path

from motherload_projet.library.paths import collections_root, ensure_dir


def _list_collections(root: Path) -> list[Path]:
    """Liste toutes les collections sous la racine."""
    collections = [path for path in root.rglob("*") if path.is_dir()]
    return sorted(collections, key=lambda path: str(path.relative_to(root)).lower())


def _is_valid_name(name: str) -> bool:
    """Valide un nom de collection."""
    if not name:
        return False
    candidate = Path(name)
    if candidate.is_absolute():
        return False
    return ".." not in candidate.parts


def choose_collection(base_dir: Path | str | None = None) -> Path | None:
    """Choisit une collection locale."""
    base_path = (
        Path(base_dir).expanduser() if base_dir is not None else collections_root()
    )
    base_path = ensure_dir(base_path)

    while True:
        collections = _list_collections(base_path)

        print("")
        print(f"Racine collections: {base_path}")
        if collections:
            for index, collection in enumerate(collections, start=1):
                rel_path = collection.relative_to(base_path)
                print(f"{index}) {rel_path}")
        else:
            print("Aucune collection.")

        print("Commandes: numero=choisir, n=nouvelle, q=quit")
        choice = input("> ").strip().lower()

        if not choice:
            continue
        if choice == "q":
            return None
        if choice == "n":
            name = input("Nom collection: ").strip()
            if not _is_valid_name(name):
                print("Nom invalide.")
                continue
            target = base_path / Path(name)
            if target.exists():
                print("La collection existe deja.")
                continue
            target.mkdir(parents=True, exist_ok=False)
            return target

        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(collections):
                return collections[index - 1]
            print("Choix invalide.")
            continue

        print("Commande inconnue.")
