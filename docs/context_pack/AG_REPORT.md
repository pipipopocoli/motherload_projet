# AG_REPORT: Sprint 1 - Acquisition Backbone (EXPANDED)

**Sprint:** Sprint 1  
**Feature:** Acquisition Backbone + Services  
**Date:** 2026-02-06  
**Agent:** Antigravity (AG)  
**Branch:** sprint-1-acquisition

---

## CODEX TODO

### Testing & CI
- [ ] Add unit tests for CSV reader (valid/invalid formats)
- [ ] Add unit tests for ArticleRecord data class
- [ ] Add integration tests for DB batch operations
- [ ] Add tests for worker thread signals
- [ ] Set up pytest configuration
- [ ] Add CI pipeline for automated testing

### API Integration (Future Sprints)
- [ ] Implement Crossref API client with httpx
- [ ] Implement OpenAlex API client
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting for API calls
- [ ] Implement caching for API responses
- [ ] Add API key management

### Error Handling & Robustness
- [ ] Add comprehensive error handling for network failures
- [ ] Implement job resume capability (save progress)
- [ ] Add validation for article metadata completeness
- [ ] Implement duplicate detection improvements
- [ ] Add data quality scoring algorithm

### UI Enhancements
- [ ] Add stop/cancel button for acquisition jobs
- [ ] Add progress bar with percentage
- [ ] Add estimated time remaining
- [ ] Add job history/log viewer
- [ ] Implement job queue management

### Performance
- [ ] Profile batch size for optimal performance
- [ ] Add connection pooling for DB
- [ ] Implement parallel journal processing
- [ ] Add memory usage monitoring

### Documentation
- [ ] Add API documentation for services
- [ ] Create user guide for acquisition workflow
- [ ] Document configuration options
- [ ] Add troubleshooting guide

---

## Context

Sprint 1 establishes the complete acquisition infrastructure for Motherload:

### Architecture
- **Core Layer**: Database models, path management (platformdirs)
- **Services Layer**: Acquisition logic, CSV reading, export/reporting
- **UI Layer**: Qt desktop app with worker threads
- **CLI Layer**: Command-line tools for automation

### Data Flow
```
inputs/journals.csv 
  → CSV Reader
  → Acquisition Job (placeholder/Crossref/OpenAlex)
  → Article Records (generator)
  → Batch DB Writer
  → Database (Application Support)
  → Export (CSV + JSON reports)
```

### Key Components
1. **app/core/**: Paths, models, DB initialization
2. **app/services/acquisition/**: CSV reader, job, DB ops, export
3. **app/workers/**: Qt worker threads for non-blocking operations
4. **app/cli.py**: CLI with init-db, run-acquisition, export-articles
5. **app/main.py**: Qt UI with acquisition button

---

## Decisions

### 1. Generator Pattern for Acquisition
Used Python generators (`yield`) for memory efficiency:
- Processes articles one at a time
- Enables streaming to database
- Supports long-running jobs (hours/days)
- Allows early termination

### 2. Batch Database Commits
Commits every 100 articles by default:
- Balances performance vs. data safety
- Prevents memory bloat
- Enables progress tracking
- Recoverable from failures

### 3. Worker Thread Pattern (Qt)
Separate thread for acquisition prevents UI freezing:
- Uses QThread with signals/slots
- Progress updates via signals
- Stoppable jobs
- Clean separation of concerns

### 4. Placeholder Implementation
Current acquisition generates dummy data:
- Allows end-to-end testing
- Validates architecture
- Real API integration in future sprint
- Clear TODO markers for Codex

### 5. Dual Interface (CLI + GUI)
Both command-line and graphical interfaces:
- CLI for automation/scripting
- GUI for interactive use
- Shared business logic
- Consistent behavior

### 6. Loguru for Logging
Chose loguru over stdlib logging:
- Simpler API
- Automatic rotation
- Better formatting
- File + console output

---

## Implementation Details

### CSV Reader (`csv_reader.py`)
- Supports both `journal_name` and `name` columns
- Validates required fields
- Handles missing/malformed data
- Returns structured dictionaries

### Acquisition Job (`job.py`)
- Generator function for memory efficiency
- ArticleRecord data class for type safety
- Placeholder yields 3 articles/year
- Ready for Crossref/OpenAlex integration

### Database Operations (`db_ops.py`)
- Batch inserts with configurable size
- Duplicate detection via DOI uniqueness
- Error tracking and reporting
- Transaction management

### Export & Reporting (`export.py`)
- CSV export with all metadata fields
- JSON coverage report with statistics
- Field completeness tracking
- Extensible report format

### Worker Thread (`acquisition_worker.py`)
- Non-blocking Qt thread
- Progress signals for UI updates
- Stoppable via flag
- Error propagation

---

## Challenges

### 1. Import Path Management
**Issue**: Python module imports from `app/` package  
**Solution**: Added `sys.path` manipulation in CLI  
**Future**: Consider proper package installation

### 2. Dependency Installation
**Issue**: Virtual environment pip broken  
**Solution**: Document manual installation steps  
**Future**: Provide setup script

### 3. Database Location
**Issue**: Permissions on Desktop  
**Solution**: Use Application Support (platformdirs)  
**Benefit**: Follows macOS best practices

### 4. UI Responsiveness
**Issue**: Long-running jobs freeze UI  
**Solution**: Worker thread with signals  
**Benefit**: Professional UX

---

## File Structure

```
app/
├── core/
│   ├── __init__.py
│   ├── paths.py          # platformdirs integration
│   └── models.py         # SQLAlchemy models
├── services/
│   ├── __init__.py
│   └── acquisition/
│       ├── __init__.py
│       ├── csv_reader.py # Journal CSV parsing
│       ├── job.py        # Acquisition generator
│       ├── db_ops.py     # Batch DB operations
│       └── export.py     # CSV/JSON export
├── workers/
│   ├── __init__.py
│   └── acquisition_worker.py  # Qt worker thread
├── cli.py               # CLI interface
└── main.py              # Qt GUI

inputs/
└── journals.csv         # Journal list

outputs/
├── articles_export.csv  # Generated by export
└── coverage_report.json # Generated by export

logs/
└── acquisition.log      # Loguru output
```

---

## Next Steps

### Sprint 2: Real API Integration
1. Implement Crossref client
2. Implement OpenAlex client
3. Add retry logic
4. Add rate limiting
5. Test with real data

### Sprint 3: PDF Acquisition
1. Integrate Unpaywall
2. Add PDF download
3. Store PDFs locally
4. Link to articles table

### Sprint 4: Advanced Features
1. Job queue management
2. Scheduled acquisitions
3. Incremental updates
4. Conflict resolution

---

## Verification

See `SPRINT1_VERIFICATION.md` for detailed commands.

### Quick Test
```bash
# Initialize database
python app/cli.py init-db

# Run acquisition (dry-run)
python app/cli.py run-acquisition --dry-run --year-from 2023 --year-to 2024

# Run acquisition (real)
python app/cli.py run-acquisition --year-from 2023 --year-to 2024

# Export articles
python app/cli.py export-articles

# Launch GUI
python app/main.py
```

---

**Status:** ✓ Sprint 1 Complete (Expanded)  
**Next Sprint:** Sprint 2 - API Integration (Crossref/OpenAlex)
