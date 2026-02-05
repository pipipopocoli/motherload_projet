# Sprint 1 - Verification Commands

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/oliviercloutier/Desktop/motherload_projet
pip install platformdirs sqlalchemy
```

### 2. Run Automated Verification
```bash
python3 verify_sprint1.py
```

Expected output:
```
============================================================
Sprint 1 - Acquisition Backbone Verification
============================================================

✓ All dependencies installed

=== Testing Database Initialization ===
✓ Database initialized at: /Users/oliviercloutier/Library/Application Support/Motherload/motherload.sqlite
✓ Tables created: journals, articles
✓ Database created at: /Users/oliviercloutier/Library/Application Support/Motherload/motherload.sqlite
  Size: [size] bytes

=== Verifying Database Schema ===
✓ Table 'journals' exists
  Columns: id, name, issn, publisher, created_at, updated_at
✓ Table 'articles' exists
  Columns: id, doi, title, authors, year, journal, abstract, url, pdf_url, source, confidence, created_at, updated_at

=== Verifying Sample Data ===
✓ journals.csv exists with 11 lines (including header)
  First line: name,issn,publisher...

=== Verifying Outputs Directory ===
✓ outputs/ directory exists

=== Verifying Documentation ===
✓ AG_REPORT.md exists
  Has CODEX TODO section: ✓

============================================================
VERIFICATION SUMMARY
============================================================
✓ PASS: Database Initialization
✓ PASS: Database Schema
✓ PASS: Sample Data
✓ PASS: Outputs Directory
✓ PASS: Documentation

Total: 5/5 tests passed

🎉 All verification tests passed!
```

## Manual Verification

### Test CLI Help
```bash
python app/cli.py --help
```

### Initialize Database
```bash
python app/cli.py init-db
```

### Check Database Location
```bash
ls -la ~/Library/Application\ Support/Motherload/
```

### Inspect Database Schema
```bash
sqlite3 ~/Library/Application\ Support/Motherload/motherload.sqlite ".schema"
```

### View Sample Journals
```bash
cat inputs/journals.csv
```

### Test Export Placeholder
```bash
python app/cli.py export-articles
```

## Git Status

### View Changes
```bash
git log --oneline -1
git show --stat
```

### Branch Info
```bash
git branch
# Should show: * sprint-1-acquisition
```

## File Structure Verification

```bash
# Check new files exist
ls -la app/core/
ls -la inputs/
ls -la outputs/
ls -la docs/context_pack/AG_REPORT.md
```

## Next Steps

After verification passes:
1. Review the walkthrough document
2. Test database initialization
3. Prepare for Sprint 2 (Journal Import)
