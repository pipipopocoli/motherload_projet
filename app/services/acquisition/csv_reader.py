"""CSV reading utilities for journal input."""

import csv
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


def read_journals_csv(csv_path: Path) -> List[Dict[str, Optional[str]]]:
    """
    Read journals from CSV file.
    
    Expected format:
        journal_name,issn (optional)
    
    Args:
        csv_path: Path to journals.csv file
        
    Returns:
        List of dictionaries with 'journal_name' and 'issn' keys
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Journals CSV not found: {csv_path}")
    
    journals = []
    
    try:
        with csv_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if 'journal_name' not in reader.fieldnames and 'name' not in reader.fieldnames:
                raise ValueError(
                    f"CSV must have 'journal_name' or 'name' column. "
                    f"Found: {reader.fieldnames}"
                )
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because header is line 1
                # Support both 'journal_name' and 'name' column names
                journal_name = row.get('journal_name') or row.get('name', '').strip()
                issn = row.get('issn', '').strip() or None
                
                if not journal_name:
                    logger.warning(f"Skipping row {row_num}: missing journal name")
                    continue
                
                journals.append({
                    'journal_name': journal_name,
                    'issn': issn
                })
        
        logger.info(f"Loaded {len(journals)} journals from {csv_path}")
        return journals
        
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")
