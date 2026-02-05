# ADR-0001: Local-first, legal-first acquisition with optional Deep Mining

Date: 2026-02-05
Status: Accepted

## Context
- The product is a macOS desktop app for a single user.
- Data must remain local and predictable.
- Some acquisition sources are legally restricted.

## Decision
- The system is local-first: all authoritative data lives under `~/Desktop/grand_librairy`.
- Network access is used only by explicit commands (for example, API lookups).
- Deep Mining is optional, isolated, and OFF by default.
- Core workflows (ingest, scan, reports) must work without Deep Mining.

## Consequences
- Clear boundaries between core features and optional acquisition.
- Easier compliance and testing.
- Additional flagging/config to gate optional behavior.
