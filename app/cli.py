#!/usr/bin/env python3
"""Command-line interface for Motherload acquisition system."""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.models import init_db


def cmd_init_db(args):
    """Initialize the database and create tables."""
    try:
        db_path = init_db()
        print(f"\n✓ Database ready at: {db_path}")
        return 0
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        return 1


def cmd_export_articles(args):
    """Export articles to CSV (placeholder for future implementation)."""
    from pathlib import Path
    from app.services.acquisition.export import export_articles_to_csv, generate_coverage_report
    
    output_path = Path("outputs/articles_export.csv")
    coverage_path = Path("outputs/coverage_report.json")
    
    try:
        count = export_articles_to_csv(output_path, limit=args.limit)
        print(f"✓ Exported {count} articles to: {output_path}")
        
        report = generate_coverage_report(coverage_path)
        print(f"✓ Coverage report: {coverage_path}")
        print(f"  Total articles: {report['total_articles']}")
        print(f"  DOI coverage: {report['coverage']['doi']['percentage']}%")
        
        return 0
    except Exception as e:
        print(f"✗ Error exporting articles: {e}", file=sys.stderr)
        return 1


def cmd_run_acquisition(args):
    """Run acquisition job for journals."""
    from pathlib import Path
    from loguru import logger
    from app.services.acquisition.csv_reader import read_journals_csv
    from app.services.acquisition.job import acquisition_job
    from app.services.acquisition.db_ops import save_articles_batch, save_journal
    from app.services.acquisition.export import export_articles_to_csv, generate_coverage_report
    
    # Setup logging
    logger.add("logs/acquisition.log", rotation="10 MB")
    
    try:
        # Read journals
        journals_path = Path(args.journals_csv or "inputs/journals.csv")
        journals = read_journals_csv(journals_path)
        
        if not journals:
            print("✗ No journals found in CSV")
            return 1
        
        print(f"✓ Loaded {len(journals)} journals")
        
        # Process each journal
        total_articles = 0
        all_stats = {'inserted': 0, 'duplicates': 0, 'errors': 0}
        
        for journal in journals:
            journal_name = journal['journal_name']
            issn = journal.get('issn')
            
            print(f"\n→ Processing: {journal_name}")
            
            # Save journal to DB
            save_journal(journal_name, issn)
            
            # Run acquisition
            articles = []
            for article in acquisition_job(
                journal_name,
                args.year_from,
                args.year_to,
                issn
            ):
                articles.append(article.to_dict())
            
            print(f"  Found {len(articles)} articles")
            
            # Save to database in batches
            if not args.dry_run:
                stats = save_articles_batch(articles)
                all_stats['inserted'] += stats['inserted']
                all_stats['duplicates'] += stats['duplicates']
                all_stats['errors'] += stats['errors']
                print(f"  Saved: {stats['inserted']} new, {stats['duplicates']} duplicates")
            else:
                print(f"  [DRY RUN] Would save {len(articles)} articles")
            
            total_articles += len(articles)
        
        # Generate outputs
        if not args.dry_run:
            print(f"\n✓ Total articles processed: {total_articles}")
            print(f"  Inserted: {all_stats['inserted']}")
            print(f"  Duplicates: {all_stats['duplicates']}")
            print(f"  Errors: {all_stats['errors']}")
            
            # Export to CSV
            output_path = Path("outputs/articles_export.csv")
            export_articles_to_csv(output_path)
            print(f"\n✓ Exported to: {output_path}")
            
            # Generate coverage report
            coverage_path = Path("outputs/coverage_report.json")
            generate_coverage_report(coverage_path, all_stats)
            print(f"✓ Coverage report: {coverage_path}")
        else:
            print(f"\n[DRY RUN] Would process {total_articles} articles total")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        logger.exception("Acquisition failed")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Motherload - Academic Article Acquisition System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/cli.py init-db              Initialize the database
  python app/cli.py export-articles      Export articles to CSV (coming soon)
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init-db command
    parser_init = subparsers.add_parser(
        "init-db",
        help="Initialize database and create tables"
    )
    parser_init.set_defaults(func=cmd_init_db)
    
    # export-articles command (placeholder)
    parser_export = subparsers.add_parser(
        "export-articles",
        help="Export articles to CSV"
    )
    parser_export.add_argument(
        "--limit",
        type=int,
        help="Limit number of articles to export"
    )
    parser_export.set_defaults(func=cmd_export_articles)
    
    # run-acquisition command
    parser_acquire = subparsers.add_parser(
        "run-acquisition",
        help="Run acquisition job for journals"
    )
    parser_acquire.add_argument(
        "--journals-csv",
        type=str,
        help="Path to journals CSV (default: inputs/journals.csv)"
    )
    parser_acquire.add_argument(
        "--year-from",
        type=int,
        default=2020,
        help="Start year (default: 2020)"
    )
    parser_acquire.add_argument(
        "--year-to",
        type=int,
        default=2024,
        help="End year (default: 2024)"
    )
    parser_acquire.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without saving to database"
    )
    parser_acquire.set_defaults(func=cmd_run_acquisition)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
