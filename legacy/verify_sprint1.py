#!/usr/bin/env python3
"""
Verification script for Sprint 1 - Acquisition Backbone
Tests database initialization and validates deliverables.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import platformdirs
    except ImportError:
        missing.append("platformdirs")
    
    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")
    
    if missing:
        print("❌ Missing dependencies:", ", ".join(missing))
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("✓ All dependencies installed")
    return True


def test_db_initialization():
    """Test database initialization."""
    print("\n=== Testing Database Initialization ===")
    
    try:
        from app.core.models import init_db
        from app.core.paths import get_db_path
        
        db_path = init_db()
        
        if db_path.exists():
            print(f"✓ Database created at: {db_path}")
            print(f"  Size: {db_path.stat().st_size} bytes")
            return True
        else:
            print(f"❌ Database not found at: {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schema():
    """Verify database schema."""
    print("\n=== Verifying Database Schema ===")
    
    try:
        import sqlite3
        from app.core.paths import get_db_path
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ["journals", "articles"]
        
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"  Columns: {', '.join(col[1] for col in columns)}")
            else:
                print(f"❌ Table '{table}' missing")
                conn.close()
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying schema: {e}")
        return False


def verify_sample_data():
    """Verify sample data files."""
    print("\n=== Verifying Sample Data ===")
    
    project_root = Path(__file__).parent
    journals_csv = project_root / "inputs" / "journals.csv"
    
    if journals_csv.exists():
        lines = journals_csv.read_text().strip().split('\n')
        print(f"✓ journals.csv exists with {len(lines)} lines (including header)")
        print(f"  First line: {lines[0][:60]}...")
        return True
    else:
        print(f"❌ journals.csv not found at: {journals_csv}")
        return False


def verify_outputs_dir():
    """Verify outputs directory."""
    print("\n=== Verifying Outputs Directory ===")
    
    project_root = Path(__file__).parent
    outputs_dir = project_root / "outputs"
    
    if outputs_dir.exists() and outputs_dir.is_dir():
        print(f"✓ outputs/ directory exists")
        return True
    else:
        print(f"❌ outputs/ directory not found")
        return False


def verify_documentation():
    """Verify documentation."""
    print("\n=== Verifying Documentation ===")
    
    project_root = Path(__file__).parent
    ag_report = project_root / "docs" / "context_pack" / "AG_REPORT.md"
    
    if ag_report.exists():
        content = ag_report.read_text()
        has_codex = "CODEX TODO" in content
        print(f"✓ AG_REPORT.md exists")
        print(f"  Has CODEX TODO section: {'✓' if has_codex else '❌'}")
        return has_codex
    else:
        print(f"❌ AG_REPORT.md not found")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Sprint 1 - Acquisition Backbone Verification")
    print("=" * 60)
    
    results = []
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠️  Install dependencies first, then re-run verification")
        return 1
    
    # Run tests
    results.append(("Database Initialization", test_db_initialization()))
    results.append(("Database Schema", verify_schema()))
    results.append(("Sample Data", verify_sample_data()))
    results.append(("Outputs Directory", verify_outputs_dir()))
    results.append(("Documentation", verify_documentation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
