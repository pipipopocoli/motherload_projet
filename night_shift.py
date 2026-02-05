"""
🎻 Le Chef d'Orchestre - Night Shift Protocol
Script d'automatisation pour "faire tourner la boutique" pendant la nuit.
"""

import time
import sys
from pathlib import Path
from motherload_projet.library.paths import bibliotheque_root
from motherload_projet.data_mining.recuperation_article.run_unpaywall_batch import run_unpaywall_csv_batch
from motherload_projet.catalogs.scanner import scan_library
from motherload_projet.local_pdf_update.local_pdf import _sanitize_filename

def log(agent: str, message: str):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] 🤖 {agent.upper()}: {message}")

def run_night_shift():
    print("==================================================")
    print("       🌑 MOTHERLOAD NIGHT SHIFT ACTIVATED 🌑       ")
    print("==================================================")
    
    # 1. THE MINER: Resume all pending downloads
    log("MINER", "Scanning specifically for 'to_be_downloaded' lists...")
    bib_root = bibliotheque_root()
    queue_files = list(bib_root.glob("to_be_downloaded_*.csv"))
    
    if not queue_files:
        log("MINER", "No queue files found. I will rest.")
    else:
        log("MINER", f"Found {len(queue_files)} queues. Putting on my helmet.")
        for qf in queue_files:
            log("MINER", f"Processing {qf.name}...")
            # Run batch with Sci-Hub fallback implied
            run_unpaywall_csv_batch(qf, bib_root, verbose_progress=False)
            log("MINER", f"Finished {qf.name}.")
            time.sleep(2) # Breath

    # 2. THE LIBRARIAN: Retro-active Cleaning
    log("LIBRARIAN", "My turn. Checking for messy files...")
    # This runs the full scan which includes _rename_with_metadata and move logic
    # We pass 'do_rename=True' (it's implicit in the current code but good to note)
    scan_library()
    log("LIBRARIAN", "Library is spotless.")

    # 3. THE CARTOGRAPHER: Re-indexing
    log("CARTOGRAPHER", "Updating the Star Map (Master Catalog)...")
    # scan_library updates the index automatically, but we can verify integrity
    log("CARTOGRAPHER", "Map updated.")

    log("CONDUCTOR", "Night Shift Complete. Going to sleep.")

if __name__ == "__main__":
    run_night_shift()
