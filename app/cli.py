#!/usr/bin/env python3
"""Command-line interface for Motherload acquisition system."""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.models import init_db
from app.core.paths import get_db_path


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
    output_path = Path("outputs/articles_export.csv")
    
    # Ensure outputs directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"⚠ Export command not yet implemented")
    print(f"  Future output will be written to: {output_path.absolute()}")
    print(f"  This will be implemented in a future sprint.")
    
    return 0


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
        help="Export articles to CSV (placeholder)"
    )
    parser_export.set_defaults(func=cmd_export_articles)
    
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
