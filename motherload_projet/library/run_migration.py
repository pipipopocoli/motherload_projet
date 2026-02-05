"""
Orchestration script for complete database migration.
Runs backup, migration, and verification in sequence.
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motherload_projet.library.backup_catalog import backup_catalog
from motherload_projet.library.migrate_db import migrate
from motherload_projet.library.verify_migration import verify


def run_full_migration():
    """Execute complete migration workflow."""
    print("\\n" + "="*60)
    print("LE CARTOGRAPHE - FULL MIGRATION WORKFLOW")
    print("="*60)
    
    # Step 1: Backup
    print("\\n[1/3] BACKUP")
    print("-" * 40)
    try:
        backup_result = backup_catalog()
        print(f"✅ Backup complete: {backup_result['backup_dir']}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        print("\\nAborting migration for safety.")
        return 1
    
    # Step 2: Migration
    print("\\n[2/3] MIGRATION")
    print("-" * 40)
    try:
        migration_result = migrate()
        if migration_result['status'] == 'error':
            print(f"❌ Migration failed: {migration_result.get('message')}")
            return 2
        print(f"✅ Migration complete: {migration_result['processed']} records")
    except Exception as e:
        print(f"❌ Migration failed with exception: {e}")
        return 2
    
    # Step 3: Verification
    print("\\n[3/3] VERIFICATION")
    print("-" * 40)
    try:
        verification_result = verify()
        if verification_result['status'] == 'success':
            print("✅ Verification passed: No issues found")
        else:
            print(f"⚠️  Verification completed with {verification_result['issues']} issues")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 3
    
    # Summary
    print("\\n" + "="*60)
    print("MIGRATION WORKFLOW COMPLETE")
    print("="*60)
    print(f"Backup: {backup_result['backup_dir']}")
    print(f"Migration Report: {migration_result.get('report_path')}")
    print(f"Verification Report: {verification_result.get('report_path')}")
    print("\\n✅ Database migration successful!")
    print("\\nNext steps:")
    print("  - Desktop app will now use SQLite automatically")
    print("  - Original CSV files remain intact as backup")
    print("  - Run 'python -m motherload_projet.desktop_app.app' to test")
    
    return 0


if __name__ == "__main__":
    exit_code = run_full_migration()
    sys.exit(exit_code)
