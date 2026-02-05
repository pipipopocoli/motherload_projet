"""
Backup script for master catalog and index before migration.
Creates timestamped backups in backups/YYYY-MM-DD/ directory.
"""

import shutil
from datetime import datetime
from pathlib import Path

from motherload_projet.library.paths import bibliotheque_root, library_root, ensure_dir


def backup_catalog():
    """Creates timestamped backup of master_catalog.csv and index.pkl."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_dir = ensure_dir(library_root() / "backups" / timestamp)
    
    bib_root = bibliotheque_root()
    
    files_to_backup = [
        bib_root / "master_catalog.csv",
        library_root() / "index.pkl",
        library_root() / "pdfs" / "index.pkl",  # Alternative location
    ]
    
    backed_up = []
    missing = []
    
    print(f"Creating backup in: {backup_dir}")
    
    for source in files_to_backup:
        if source.exists():
            dest = backup_dir / source.name
            shutil.copy2(source, dest)
            backed_up.append(source.name)
            print(f"✓ Backed up: {source.name} ({source.stat().st_size} bytes)")
        else:
            missing.append(source.name)
    
    # Create backup manifest
    manifest = backup_dir / "backup_manifest.txt"
    with manifest.open("w") as f:
        f.write(f"Backup created: {datetime.now().isoformat()}\\n")
        f.write(f"\\nBacked up files:\\n")
        for name in backed_up:
            f.write(f"  - {name}\\n")
        if missing:
            f.write(f"\\nMissing files (not backed up):\\n")
            for name in missing:
                f.write(f"  - {name}\\n")
    
    print(f"\\nBackup complete: {backup_dir}")
    print(f"Files backed up: {len(backed_up)}")
    if missing:
        print(f"Files missing: {len(missing)}")
    
    return {
        "backup_dir": str(backup_dir),
        "backed_up": backed_up,
        "missing": missing,
        "timestamp": timestamp
    }


if __name__ == "__main__":
    result = backup_catalog()
    print(f"\\nBackup directory: {result['backup_dir']}")
