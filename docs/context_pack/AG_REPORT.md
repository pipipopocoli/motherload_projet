# AG_REPORT: Sprint 1 - Acquisition Backbone

**Sprint:** Sprint 1  
**Feature:** Acquisition Backbone  
**Date:** 2026-02-06  
**Agent:** Antigravity (AG)

---

## CODEX TODO

- [ ] Implement journal CSV import functionality
- [ ] Add article acquisition from Unpaywall/SciHub
- [ ] Implement confidence scoring algorithm
- [ ] Add Deep Mining interface flags (external only)
- [ ] Create article export to CSV functionality
- [ ] Add batch processing for journal lists
- [ ] Implement error handling and retry logic
- [ ] Add progress tracking for long-running operations

---

## Context

This sprint establishes the foundational infrastructure for the Motherload acquisition system:

- **Database:** SQLite stored in `~/Library/Application Support/Motherload/` using platformdirs
- **Models:** SQLAlchemy ORM for Journals and Articles tables
- **CLI:** Command-line interface for database initialization and future exports
- **Data Flow:** CSV input → Processing → Database → CSV export

---

## Decisions

### Database Location
Chose `~/Library/Application Support/Motherload/` following macOS best practices for application data. This ensures:
- Proper permissions without sudo
- Standard location for user data
- Compatibility with sandboxing if needed later

### SQLAlchemy vs Raw SQLite
Selected SQLAlchemy for:
- Type safety and ORM benefits
- Easier migrations in future sprints
- Better integration with Python ecosystem

### CSV as Input Format (v1)
Mandatory CSV input for journals aligns with:
- Easy data preparation from existing sources
- Simple validation and debugging
- Future migration path to other formats

---

## Challenges

### Deep Mining Isolation
Per constraints, Deep Mining internals are not modified. Only external interfaces and flags will be added in future sprints when integration is needed.

### Confidence Scoring
Article confidence field (0.0-1.0) is prepared but algorithm not yet implemented. Will be defined based on:
- Metadata completeness
- Source reliability
- Cross-reference validation

---

## Next Steps

1. **Sprint 2:** Implement journal CSV import
2. **Sprint 3:** Add article acquisition from external sources
3. **Sprint 4:** Implement confidence scoring
4. **Sprint 5:** Complete export functionality
5. **Future:** Deep Mining integration via external interfaces

---

## Verification

```bash
# Initialize database
python app/cli.py init-db

# Verify database location
ls -la ~/Library/Application\ Support/Motherload/

# Check schema
sqlite3 ~/Library/Application\ Support/Motherload/motherload.sqlite ".schema"

# View sample journals
cat inputs/journals.csv
```

---

**Status:** ✓ Sprint 1 Complete  
**Next Sprint:** Sprint 2 - Journal Import
