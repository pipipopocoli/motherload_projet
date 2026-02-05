"""Module de verification de la sante des fichiers PDF."""

from __future__ import annotations

import shutil
from pathlib import Path

from motherload_projet.data_mining.pdf_validate import validate_pdf_bytes
from motherload_projet.library.paths import ensure_dir


def check_library_health(
    root_dir: Path, quarantine_dir: Path | None = None, move_corrupt: bool = False
) -> dict[str, int]:
    """
    Scanne recursif un dossier pour trouver les PDFs corrompus.
    
    Args:
        root_dir: Dossier racine a scanner.
        quarantine_dir: Dossier ou deplacer les fichiers corrompus (optionnel).
        move_corrupt: Si True, deplace les fichiers corrompus vers quarantine_dir.
        
    Returns:
        Dict avec stats (total, ok, corrupt, empty, not_pdf).
    """
    stats = {
        "total": 0,
        "ok": 0,
        "corrupt": 0,
        "empty": 0,
        "not_pdf": 0,
        "moved": 0,
    }
    
    if not root_dir.exists():
        print(f"Dossier introuvable: {root_dir}")
        return stats
        
    if move_corrupt and quarantine_dir:
        ensure_dir(quarantine_dir)
        
    print(f"Scan de sante demarre sur: {root_dir}")
    
    for path in root_dir.rglob("*.pdf"):
        stats["total"] += 1
        
        try:
            content = path.read_bytes()
            is_valid, reason = validate_pdf_bytes(content)
            
            if is_valid:
                stats["ok"] += 1
                continue
                
            print(f"[CORRUPT] {reason}: {path.name} ({path})")
            stats["corrupt"] += 1
            if reason == "EMPTY":
                stats["empty"] += 1
            elif reason == "NOT_PDF":
                stats["not_pdf"] += 1
                
            if move_corrupt and quarantine_dir:
                try:
                    target = quarantine_dir / path.name
                    # Eviter ecrasement
                    if target.exists():
                        target = quarantine_dir / f"CORRUPT_{path.stem}_{reason}{path.suffix}"
                        
                    shutil.move(str(path), str(target))
                    print(f" -> Deplace vers: {target}")
                    stats["moved"] += 1
                except Exception as e:
                    print(f" -> Erreur lors du deplacement: {e}")
                    
        except Exception as e:
            print(f"[ERROR] Impossible de lire {path}: {e}")
            stats["corrupt"] += 1
            
    print("\n--- Bilan de Sante ---")
    print(f"Total scanne : {stats['total']}")
    print(f"Sains        : {stats['ok']}")
    print(f"Corrompus    : {stats['corrupt']}")
    print(f"  - Vides    : {stats['empty']}")
    print(f"  - Pas PDF  : {stats['not_pdf']}")
    if move_corrupt:
        print(f"Deplaces     : {stats['moved']}")
        
    return stats
