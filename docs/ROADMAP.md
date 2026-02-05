# Motherload - Product Roadmap

**Version:** 1.0  
**Last Updated:** 2026-02-06  
**Owner:** Product/Engineering Lead

---

## Vision

Build a **robust, local-first desktop application** for academic article acquisition and library management with:
- High metadata coverage (>90% complete records)
- Reliable long-running jobs (hours/days)
- Legal-first approach with optional Deep Mining
- Professional desktop UX (Qt)

---

## North Star Metrics

### Coverage (Primary)
- **Target:** 90%+ articles with complete metadata (DOI, title, authors, year, journal, abstract, URL)
- **Measurement:** Coverage score per article, aggregated per journal and globally
- **Reporting:** JSON coverage report + CSV export

### Reliability (Secondary)
- **Target:** 95%+ job completion rate (no crashes)
- **Measurement:** Jobs completed / jobs started
- **Reporting:** Job history with success/failure stats

### Performance (Tertiary)
- **Target:** Process 1000 articles/hour (metadata only)
- **Measurement:** Articles processed / time
- **Reporting:** Performance logs

---

## Phases

### Phase 1: Foundation (CURRENT - Sprint 1-2)
**Goal:** Stable acquisition backbone with legal sources

**Deliverables:**
- ✅ Database infrastructure (SQLite + SQLAlchemy)
- ✅ Basic acquisition skeleton (placeholder)
- ✅ Qt UI with worker threads
- ✅ CLI interface
- 🔄 Coverage calculation & reporting (PR #1)
- 🔄 Robustness (retry/backoff/logging) (PR #2)
- 🔄 Deduplication (DOI + soft) (PR #3)
- 🔄 Enhanced Qt worker with progress (PR #4)
- 🔄 CLI debug commands (PR #5)
- 🔄 Deep Mining isolation + feature flag (PR #6)

**Success Criteria:**
- Coverage report shows >80% for test dataset
- Jobs run for 1+ hour without crashing
- UI remains responsive
- Deep Mining works when enabled (flag OFF by default)

---

### Phase 2: API Integration (Sprint 3-4)
**Goal:** Real data acquisition from legal APIs

**Deliverables:**
- Crossref API client (with retry/rate limit)
- OpenAlex API client
- Unpaywall integration
- API key management
- Caching layer
- Fallback chain: OpenAlex → Crossref → Unpaywall → [Deep Mining]

**Success Criteria:**
- Coverage >90% for major journals
- Rate limits respected
- API errors handled gracefully

---

### Phase 3: PDF Acquisition (Sprint 5-6)
**Goal:** Download PDFs where legally available

**Deliverables:**
- Unpaywall PDF download
- Institutional access support (proxy)
- PDF storage + organization
- PDF health checks
- Deep Mining PDF fallback (behind flag)

**Success Criteria:**
- 50%+ articles have PDFs
- PDFs validated and healthy
- Storage organized by journal/year

---

### Phase 4: Library & Search (Sprint 7-9)
**Goal:** Manage and search acquired articles

**Deliverables:**
- Full-text search (SQLite FTS5)
- Tag/collection management
- Notes system
- Export formats (BibTeX, RIS)
- Backup/restore

**Success Criteria:**
- Search <100ms for 10k articles
- Collections work smoothly
- Export formats valid

---

### Phase 5: Advanced Features (Sprint 10+)
**Goal:** Power user features

**Deliverables:**
- Scheduled acquisitions
- Incremental updates
- Citation network analysis
- Reading recommendations
- Mobile companion (optional)

---

## Sprint Breakdown

### Sprint 1 (COMPLETED)
- ✅ Core infrastructure
- ✅ Basic acquisition skeleton
- ✅ Qt UI + worker threads
- ✅ CLI commands

### Sprint 2 (CURRENT - 3-4 weeks)
- 🔄 PR #1: Coverage & Reporting
- 🔄 PR #2: Robustness & Error Handling
- 🔄 PR #3: Deduplication & DB Operations
- 🔄 PR #4: Qt Worker & Progress UI
- 🔄 PR #5: CLI Debug & Verification
- 🔄 PR #6: Deep Mining Isolation

### Sprint 3 (Future)
- Crossref API integration
- OpenAlex API integration
- API testing with real data

### Sprint 4 (Future)
- Unpaywall integration
- Caching layer
- Performance optimization

---

## Modules

### Core (`app/core/`)
- **Responsibility:** Database, models, paths
- **Owner:** Platform team
- **Stability:** High (changes require migration)

### Services (`app/services/`)
- **Responsibility:** Business logic (acquisition, export, dedup)
- **Owner:** Features team
- **Stability:** Medium (evolving)

### Workers (`app/workers/`)
- **Responsibility:** Background tasks (Qt threads)
- **Owner:** UI team
- **Stability:** Medium

### Deep Mining (`app/services/deep_mining/`)
- **Responsibility:** SciHub, Tor, restricted sources
- **Owner:** Features team (restricted)
- **Stability:** Low (isolated, feature-flagged)
- **Access:** Behind feature flag, OFF by default

### UI (`app/main.py`, `app/widgets/`)
- **Responsibility:** Qt desktop interface
- **Owner:** UI team
- **Stability:** Medium

### CLI (`app/cli.py`)
- **Responsibility:** Command-line tools
- **Owner:** DevOps/Features team
- **Stability:** High (backward compatible)

---

## Definition of Done (DoD)

### For All PRs
- [ ] Code reviewed by 1+ team member
- [ ] Tests pass (unit + integration)
- [ ] Documentation updated
- [ ] "How to verify" section complete
- [ ] No new lint errors
- [ ] Changelog entry added

### For Feature PRs
- [ ] Coverage metrics included
- [ ] Performance benchmarks (if applicable)
- [ ] UI screenshots/video (if applicable)
- [ ] Migration script (if DB changes)
- [ ] Backward compatibility verified

---

## Metrics Dashboard

### Coverage Metrics
- **Articles with DOI:** X / Y (Z%)
- **Articles with abstract:** X / Y (Z%)
- **Articles with PDF URL:** X / Y (Z%)
- **Overall coverage score:** X%

### Reliability Metrics
- **Jobs completed:** X / Y (Z%)
- **Average job duration:** X minutes
- **Errors per 1000 articles:** X

### Performance Metrics
- **Articles/hour:** X
- **API calls/minute:** X
- **DB writes/second:** X

---

## Technical Debt

### High Priority
- [ ] Add comprehensive test suite (PR #7)
- [ ] Set up CI/CD pipeline
- [ ] Add performance profiling

### Medium Priority
- [ ] Refactor legacy code in `motherload_projet/`
- [ ] Consolidate duplicate functionality
- [ ] Improve error messages

### Low Priority
- [ ] Code style consistency
- [ ] Documentation completeness
- [ ] Logging standardization

---

## Risks & Mitigations

### Risk 1: API Rate Limits
**Impact:** High  
**Probability:** High  
**Mitigation:** Implement rate limiting, caching, fallback sources

### Risk 2: Deep Mining Legal Issues
**Impact:** Critical  
**Probability:** Medium  
**Mitigation:** Feature flag OFF by default, clear warnings, isolated code, legal disclaimer

### Risk 3: Long-Running Job Failures
**Impact:** High  
**Probability:** Medium  
**Mitigation:** Retry logic, job state persistence, graceful error handling

### Risk 4: Database Performance
**Impact:** Medium  
**Probability:** Low  
**Mitigation:** Batch operations, indexes, connection pooling

### Risk 5: UI Freezing
**Impact:** High  
**Probability:** Low (mitigated)  
**Mitigation:** Worker threads, progress updates, graceful stop

---

## Next Steps

1. **Immediate (This Week):**
   - Start PR #1 (Coverage & Reporting)
   - Start PR #2 (Robustness & Error Handling)
   - Create SPEC_ACQUISITION.md

2. **Short Term (Next 2 Weeks):**
   - Complete PR #1, #2
   - Start PR #3, #6
   - Update STATE.md weekly

3. **Medium Term (Next Month):**
   - Complete all 6 PRs
   - Begin Sprint 3 (API integration)
   - Measure coverage metrics

---

**Status:** Phase 1 in progress  
**Next Review:** Weekly sprint sync
