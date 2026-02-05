"""
Verification script for Librarium migration.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

from motherload_projet.library.models import get_connection
from motherload_projet.library.paths import bibliotheque_root, ensure_dir, reports_root


def verify():
    """Comprehensive verification of migration."""
    print("="*60)
    print("LE CARTOGRAPHE - MIGRATION VERIFICATION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    verification_results = {}
    issues = []
    
    # Load original CSV for comparison
    csv_path = bibliotheque_root() / "master_catalog.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        csv_dois = set(str(doi).strip() for doi in df['doi'].dropna() if str(doi).strip() and str(doi).lower() != 'nan')
        verification_results['csv_total'] = len(df)
        verification_results['csv_dois'] = len(csv_dois)
    else:
        print("Warning: master_catalog.csv not found, skipping comparison")
        csv_dois = set()
        verification_results['csv_total'] = 0
        verification_results['csv_dois'] = 0

    print("\n--- DATABASE INTEGRITY CHECK ---")
    
    # Check total papers
    cursor.execute("SELECT COUNT(*) FROM papers")
    total_papers = cursor.fetchone()[0]
    verification_results['db_papers'] = total_papers
    print(f"Total Papers in DB: {total_papers}")
    
    # Check total Authors
    cursor.execute("SELECT COUNT(*) FROM authors")
    total_authors = cursor.fetchone()[0]
    verification_results['db_authors'] = total_authors
    print(f"Total Authors: {total_authors}")
    
    # Check total Collections
    cursor.execute("SELECT COUNT(*) FROM collections")
    total_collections = cursor.fetchone()[0]
    verification_results['db_collections'] = total_collections
    print(f"Total Collections: {total_collections}")
    
    # Check total Tags
    cursor.execute("SELECT COUNT(*) FROM tags")
    total_tags = cursor.fetchone()[0]
    verification_results['db_tags'] = total_tags
    print(f"Total Tags: {total_tags}")

    # DOI Coverage Check
    print("\n--- DOI COVERAGE CHECK ---")
    cursor.execute("SELECT doi FROM papers")
    db_dois = set(row[0] for row in cursor.fetchall())
    verification_results['db_dois'] = len(db_dois)
    
    if csv_dois:
        missing_dois = csv_dois - db_dois
        extra_dois = db_dois - csv_dois
        coverage = (len(db_dois) / len(csv_dois) * 100) if csv_dois else 0
        
        verification_results['doi_coverage'] = coverage
        verification_results['missing_dois'] = len(missing_dois)
        verification_results['extra_dois'] = len(extra_dois)
        
        print(f"CSV DOIs: {len(csv_dois)}")
        print(f"DB DOIs: {len(db_dois)}")
        print(f"Coverage: {coverage:.2f}%")
        
        if missing_dois:
            print(f"\n⚠️  Missing DOIs: {len(missing_dois)}")
            issues.append(f"Missing {len(missing_dois)} DOIs from CSV")
            for doi in list(missing_dois)[:5]:
                print(f"  - {doi}")
            if len(missing_dois) > 5:
                print(f"  ... and {len(missing_dois) - 5} more")
        
        if extra_dois:
            print(f"\nExtra DOIs in DB (not in CSV): {len(extra_dois)}")
            for doi in list(extra_dois)[:5]:
                print(f"  - {doi}")
        
        if coverage == 100.0 and not missing_dois:
            print("✅ 100% DOI coverage - No data loss!")
        else:
            issues.append(f"DOI coverage is {coverage:.2f}%, expected 100%")

    # Relationship Validation
    print("\n--- RELATIONSHIP VALIDATION ---")
    
    # Check orphaned authors (authors with no papers)
    cursor.execute("""
        SELECT COUNT(*) FROM authors a
        WHERE NOT EXISTS (
            SELECT 1 FROM paper_authors pa WHERE pa.author_id = a.id
        )
    """)
    orphaned_authors = cursor.fetchone()[0]
    verification_results['orphaned_authors'] = orphaned_authors
    if orphaned_authors > 0:
        print(f"⚠️  Orphaned authors: {orphaned_authors}")
        issues.append(f"{orphaned_authors} authors with no papers")
    else:
        print(f"✅ No orphaned authors")
    
    # Check papers without authors
    cursor.execute("""
        SELECT COUNT(*) FROM papers p
        WHERE NOT EXISTS (
            SELECT 1 FROM paper_authors pa WHERE pa.paper_id = p.id
        )
    """)
    papers_no_authors = cursor.fetchone()[0]
    verification_results['papers_no_authors'] = papers_no_authors
    print(f"Papers without authors: {papers_no_authors}")
    
    # Check papers without collections
    cursor.execute("""
        SELECT COUNT(*) FROM papers p
        WHERE NOT EXISTS (
            SELECT 1 FROM paper_collections pc WHERE pc.paper_id = p.id
        )
    """)
    papers_no_collections = cursor.fetchone()[0]
    verification_results['papers_no_collections'] = papers_no_collections
    print(f"Papers without collections: {papers_no_collections}")

    print("\n--- TOP 10 AUTHORS ---")
    try:
        cursor.execute("""
            SELECT a.name, COUNT(pa.paper_id) as count
            FROM authors a
            JOIN paper_authors pa ON a.id = pa.author_id
            GROUP BY a.id
            ORDER BY count DESC
            LIMIT 10
        """)
        for rank, (name, count) in enumerate(cursor.fetchall(), 1):
            print(f"{rank}. {name}: {count} papers")
    except Exception as e:
        print(f"Error querying authors: {e}")
        issues.append(f"Error querying top authors: {e}")

    print("\n--- TOP 5 YEARS ---")
    try:
        cursor.execute("""
            SELECT year, COUNT(*) as count
            FROM papers
            WHERE year IS NOT NULL AND year != ''
            GROUP BY year
            ORDER BY count DESC
            LIMIT 5
        """)
        for rank, (year, count) in enumerate(cursor.fetchall(), 1):
            print(f"{rank}. {year}: {count} papers")
    except Exception as e:
        print(f"Error querying years: {e}")
        issues.append(f"Error querying years: {e}")
    
    print("\n--- TOP 5 COLLECTIONS ---")
    try:
        cursor.execute("""
            SELECT c.name, COUNT(pc.paper_id) as count
            FROM collections c
            JOIN paper_collections pc ON c.id = pc.collection_id
            GROUP BY c.id
            ORDER BY count DESC
            LIMIT 5
        """)
        for rank, (name, count) in enumerate(cursor.fetchall(), 1):
            print(f"{rank}. {name}: {count} papers")
    except Exception as e:
        print(f"Error querying collections: {e}")

    conn.close()
    
    # Generate verification report
    report_path = _generate_verification_report(verification_results, issues)
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print(f"Report: {report_path}")
    
    if not issues:
        print("✅ All checks passed!")
        return {"status": "success", "issues": 0, "report_path": str(report_path)}
    else:
        print(f"⚠️  Found {len(issues)} issues")
        return {"status": "warning", "issues": len(issues), "report_path": str(report_path)}


def _generate_verification_report(results, issues):
    """Generate verification report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = ensure_dir(reports_root())
    report_path = report_dir / f"verification_report_{timestamp}.txt"
    
    with report_path.open("w") as f:
        f.write("="*60 + "\n")
        f.write("LE CARTOGRAPHE - VERIFICATION REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("DATABASE STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Papers: {results.get('db_papers', 0)}\n")
        f.write(f"Authors: {results.get('db_authors', 0)}\n")
        f.write(f"Collections: {results.get('db_collections', 0)}\n")
        f.write(f"Tags: {results.get('db_tags', 0)}\n\n")
        
        if results.get('csv_total', 0) > 0:
            f.write("DATA INTEGRITY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Original CSV rows: {results['csv_total']}\n")
            f.write(f"CSV DOIs: {results['csv_dois']}\n")
            f.write(f"DB DOIs: {results['db_dois']}\n")
            f.write(f"DOI Coverage: {results.get('doi_coverage', 0):.2f}%\n")
            f.write(f"Missing DOIs: {results.get('missing_dois', 0)}\n\n")
        
        f.write("RELATIONSHIP INTEGRITY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Orphaned authors: {results.get('orphaned_authors', 0)}\n")
        f.write(f"Papers without authors: {results.get('papers_no_authors', 0)}\n")
        f.write(f"Papers without collections: {results.get('papers_no_collections', 0)}\n\n")
        
        if issues:
            f.write("ISSUES FOUND\n")
            f.write("-" * 40 + "\n")
            for issue in issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("✅ NO ISSUES FOUND\n")
    
    return report_path


if __name__ == "__main__":
    result = verify()
    if result:
        print(f"\nStatus: {result['status']}")

