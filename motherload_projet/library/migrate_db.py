"""
Script to migrate data from master_catalog.csv to librarium.db.
"""

import sqlite3
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from motherload_projet.library.models import get_connection, init_db
from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root

def migrate():
    """Migrates data from CSV to SQLite."""
    start_time = time.time()
    migration_log = []
    
    print("="*60)
    print("LE CARTOGRAPHE - DATABASE MIGRATION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nInitializing database...")
    init_db()
    migration_log.append(f"Database initialized at {datetime.now().isoformat()}")
    
    csv_path = bibliotheque_root() / "master_catalog.csv"
    if not csv_path.exists():
        error_msg = f"Error: {csv_path} not found."
        print(error_msg)
        migration_log.append(error_msg)
        return {"status": "error", "message": error_msg}

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Migrating data...")
    
    # Helper to get or create related entity
    def get_or_create_id(table, col, value):
        if not value:
            return None
        value = value.strip()
        cursor.execute(f"SELECT id FROM {table} WHERE {col} = ?", (value,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute(f"INSERT INTO {table} ({col}) VALUES (?)", (value,))
        return cursor.lastrowid

    count = 0
    errors = 0
    error_details = []
    skipped_no_doi = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Migrating records"):
        try:
            doi = str(row.get("doi", "")).strip()
            if not doi or doi.lower() == "nan":
                # Fallback for manual entries without DOI, use title/year hash concept or skip?
                # For now, we require DOI or we skip/log. 
                # Actually, some entries might not have DOI but are valuable.
                # Let's generate a pseudo-DOI if missing or use a separate ID logic.
                # The schema enforces UNIQUE DOI.
                # If no DOI, we might skip implementation for strictness or use a placeholder.
                # Let's check if title exists.
                title = str(row.get("title", "")).strip()
                if title:
                     # Generate a local ID for non-DOI items if needed, but schema says DOI UNIQUE NOT NULL.
                     # We will skip items without DOI for the strict 'Cartographe' mandate ("Unique DOI").
                     # Or we can use the 'primary_id' or hash if available as the DOI placeholder.
                     pass
                if not doi:
                    skipped_no_doi += 1
                    continue

            # Upsert Paper
            # We use INSERT OR IGNORE or INSERT OR REPLACE. 
            # Given we want to update if exists:
            cursor.execute("""
                INSERT INTO papers (
                    doi, title, year, abstract, journal, volume, issue, pages, 
                    publisher, pdf_path, file_hash, url, added_at, source, 
                    status, type, is_oa, oa_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doi) DO UPDATE SET
                    title=excluded.title,
                    year=excluded.year,
                    abstract=excluded.abstract,
                    pdf_path=excluded.pdf_path,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                doi,
                row.get("title"),
                row.get("year"),
                row.get("abstract"),
                row.get("journal"),
                row.get("volume"),
                row.get("issue"),
                row.get("pages"),
                row.get("publisher"),
                row.get("pdf_path"),
                row.get("file_hash"),
                row.get("url"),
                row.get("added_at"),
                row.get("source"),
                row.get("status"),
                row.get("type"),
                str(row.get("is_oa")),
                row.get("oa_status")
            ))
            
            # Get the paper_id (it exists now)
            cursor.execute("SELECT id FROM papers WHERE doi = ?", (doi,))
            paper_id = cursor.fetchone()[0]
            
            # Handle Authors
            authors_str = str(row.get("authors", ""))
            if authors_str and authors_str.lower() != "nan":
                # Split by semicolon usually
                authors = [a.strip() for a in authors_str.split(";") if a.strip()]
                for author in authors:
                    author_id = get_or_create_id("authors", "name", author)
                    if author_id:
                        cursor.execute("INSERT OR IGNORE INTO paper_authors (paper_id, author_id) VALUES (?, ?)", (paper_id, author_id))

            # Handle Collections
            coll_str = str(row.get("collection", ""))
            if coll_str and coll_str.lower() != "nan":
                # Sometimes collection might be multiple? Assuming single for now based on previous CSV peek/code
                # But CSV peek showed just "AGI_review_test". 
                # Let's assume separated by semi-colon just in case, or single.
                collections = [c.strip() for c in coll_str.split(";") if c.strip()]
                for coll in collections:
                    coll_id = get_or_create_id("collections", "name", coll)
                    if coll_id:
                        cursor.execute("INSERT OR IGNORE INTO paper_collections (paper_id, collection_id) VALUES (?, ?)", (paper_id, coll_id))

            # Handle Tags / Keywords
            kw_str = str(row.get("keywords", ""))
            if kw_str and kw_str.lower() != "nan":
                # Split by semi-colon
                keywords = [k.strip() for k in kw_str.split(";") if k.strip()]
                for kw in keywords:
                    tag_id = get_or_create_id("tags", "name", kw)
                    if tag_id:
                        cursor.execute("INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))
            
            count += 1
            if count % 100 == 0:
                conn.commit()

        except Exception as e:
            errors += 1
            error_msg = f"Row {idx}: {doi if doi else 'NO_DOI'} - {str(e)}"
            error_details.append(error_msg)
            if errors <= 10:  # Only print first 10 errors to avoid spam
                print(f"\nError: {error_msg}")

    conn.commit()
    conn.close()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"Total records processed: {count}")
    print(f"Skipped (no DOI): {skipped_no_doi}")
    print(f"Errors: {errors}")
    print(f"Execution time: {elapsed_time:.2f} seconds")
    print(f"Average: {elapsed_time/len(df):.3f} sec/record")
    
    # Generate migration report
    report_path = _generate_migration_report(
        count, skipped_no_doi, errors, error_details, elapsed_time, len(df)
    )
    print(f"\nMigration report: {report_path}")
    
    return {
        "status": "success" if errors == 0 else "partial",
        "processed": count,
        "skipped": skipped_no_doi,
        "errors": errors,
        "elapsed_time": elapsed_time,
        "report_path": str(report_path)
    }


def _generate_migration_report(count, skipped, errors, error_details, elapsed_time, total_rows):
    """Generate detailed migration report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = ensure_dir(reports_root())
    report_path = report_dir / f"migration_report_{timestamp}.txt"
    
    with report_path.open("w") as f:
        f.write("="*60 + "\n")
        f.write("LE CARTOGRAPHE - MIGRATION REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total CSV rows: {total_rows}\n")
        f.write(f"Successfully migrated: {count}\n")
        f.write(f"Skipped (no DOI): {skipped}\n")
        f.write(f"Errors: {errors}\n")
        f.write(f"Success rate: {(count/total_rows*100):.2f}%\n")
        f.write(f"Execution time: {elapsed_time:.2f} seconds\n")
        f.write(f"Average speed: {elapsed_time/total_rows:.3f} sec/record\n\n")
        
        if error_details:
            f.write("ERROR DETAILS\n")
            f.write("-" * 40 + "\n")
            for error in error_details:
                f.write(f"  - {error}\n")
    
    return report_path


if __name__ == "__main__":
    result = migrate()
    if result:
        print(f"\nStatus: {result['status']}")
