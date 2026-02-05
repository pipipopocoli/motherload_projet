# Sprint 1 - Acquisition Backbone: Verification Guide

## Prerequisites

```bash
cd /Users/oliviercloutier/Desktop/motherload_projet

# Install dependencies
pip install platformdirs sqlalchemy httpx loguru PySide6
```

## 1. Database Initialization

```bash
python app/cli.py init-db
```

**Expected Output:**
```
✓ Database initialized at: /Users/oliviercloutier/Library/Application Support/Motherload/motherload.sqlite
✓ Tables created: journals, articles
```

**Verify:**
```bash
ls -la ~/Library/Application\ Support/Motherload/
sqlite3 ~/Library/Application\ Support/Motherload/motherload.sqlite ".schema"
```

## 2. Dry-Run Acquisition

```bash
python app/cli.py run-acquisition --dry-run --year-from 2023 --year-to 2024
```

**Expected Output:**
```
✓ Loaded 10 journals

→ Processing: Nature
  Found 6 articles
  [DRY RUN] Would save 6 articles

→ Processing: Science
  Found 6 articles
  [DRY RUN] Would save 6 articles

...

[DRY RUN] Would process 60 articles total
```

## 3. Real Acquisition (Placeholder Data)

```bash
python app/cli.py run-acquisition --year-from 2023 --year-to 2024
```

**Expected Output:**
```
✓ Loaded 10 journals

→ Processing: Nature
  Found 6 articles
  Saved: 6 new, 0 duplicates

...

✓ Total articles processed: 60
  Inserted: 60
  Duplicates: 0
  Errors: 0

✓ Exported to: outputs/articles_export.csv
✓ Coverage report: outputs/coverage_report.json
```

## 4. Verify Outputs

```bash
# Check CSV export
cat outputs/articles_export.csv | head -n 5

# Check coverage report
cat outputs/coverage_report.json
```

**Expected JSON Structure:**
```json
{
  "generated_at": "2024-02-06T...",
  "total_articles": 60,
  "coverage": {
    "doi": {"count": 60, "percentage": 100.0},
    "abstract": {"count": 60, "percentage": 100.0},
    "pdf_url": {"count": 0, "percentage": 0.0}
  },
  "missing_fields": {
    "doi": 0,
    "abstract": 0,
    "pdf_url": 60
  },
  "job_stats": {
    "inserted": 60,
    "duplicates": 0,
    "errors": 0
  }
}
```

## 5. Export Articles

```bash
python app/cli.py export-articles --limit 10
```

**Expected Output:**
```
✓ Exported 10 articles to: outputs/articles_export.csv
✓ Coverage report: outputs/coverage_report.json
  Total articles: 60
  DOI coverage: 100.0%
```

## 6. Launch Qt GUI

```bash
python app/main.py
```

**Expected Behavior:**
1. Window opens with 3-column layout
2. Left panel has "Run Acquisition" button
3. Click button → Progress log shows acquisition
4. UI remains responsive during acquisition
5. Completion message shows statistics

## 7. Verify Database Contents

```bash
sqlite3 ~/Library/Application\ Support/Motherload/motherload.sqlite

# SQL commands:
SELECT COUNT(*) FROM journals;
SELECT COUNT(*) FROM articles;
SELECT * FROM journals LIMIT 5;
SELECT doi, title, year FROM articles LIMIT 5;
.quit
```

## 8. Check Logs

```bash
cat logs/acquisition.log
```

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError: No module named 'app'`:
- Ensure you're running from project root
- CLI adds project root to sys.path automatically

### Database Permission Errors
If database creation fails:
- Check `~/Library/Application Support/` permissions
- platformdirs should handle this automatically

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Qt Display Issues
If GUI doesn't appear:
- Check PySide6 installation
- Try: `python -c "from PySide6.QtWidgets import QApplication; print('OK')"`

## Success Criteria

- ✅ Database created in Application Support
- ✅ Journals and articles tables exist
- ✅ Dry-run completes without errors
- ✅ Real acquisition saves to database
- ✅ CSV export generates valid file
- ✅ Coverage report shows statistics
- ✅ Qt GUI launches and runs acquisition
- ✅ UI remains responsive during job
- ✅ Logs written to logs/acquisition.log

## Next Steps

After verification:
1. Review code structure
2. Plan Sprint 2 (API integration)
3. Identify improvements
4. Document any issues
