
from motherload_projet.library.paths import bibliotheque_root, ensure_dir
from pathlib import Path

try:
    path = bibliotheque_root()
    print(f"Bibliotheque Root: {path}")
    print(f"Exists: {path.exists()}")
    
    db_path = path / "librarium.db"
    print(f"Target DB Path: {db_path}")
    
    # Try creating dir if not exists
    if not path.exists():
        print("Creating directory...")
        ensure_dir(path)
        print(f"Created. Exists: {path.exists()}")
    
    # Try touching the file
    print("Touching file...")
    db_path.touch()
    print("Success.")
except Exception as e:
    print(f"Error: {e}")
