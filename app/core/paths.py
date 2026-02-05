"""Path management using platformdirs for macOS Application Support."""

from pathlib import Path
from platformdirs import user_data_dir


APP_NAME = "Motherload"
APP_AUTHOR = "Motherload"


def get_app_data_dir() -> Path:
    """
    Returns the application data directory.
    
    On macOS: ~/Library/Application Support/Motherload/
    """
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """
    Returns the path to the SQLite database.
    
    Returns:
        Path to motherload.sqlite in Application Support directory
    """
    return get_app_data_dir() / "motherload.sqlite"


def ensure_dir(path: Path) -> Path:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        The same path for chaining
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
