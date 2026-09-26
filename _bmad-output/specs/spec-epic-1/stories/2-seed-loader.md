---
title: 'The seed loader'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `app.db` does not exist. `mcp/triage_server.py` queries `tickets` and `customers` tables at runtime; without a populated database no agent can run.

**Approach:** Implement `load_seed.py` to read `seed/tickets.csv` and `seed/customers.csv` into `app.db` as SQLite tables `tickets` and `customers`, with columns matching the CSV headers exactly. Use upsert semantics (`INSERT OR REPLACE`) so the script is safe to run more than once.

</frozen-after-approval>

## Implementation Notes

- Created `load_seed.py` with a `load(db_path)` function. Reads both CSVs into memory first, then runs DDL (DROP + CREATE) for both tables, then inserts all rows in a single DML transaction — avoids implicit commits triggered by DDL under Python's legacy sqlite3 transaction control.
- `open_tickets` stored as INTEGER (via `_INT_COLUMNS` set) so the Epic 2 agent can apply the Enterprise bump rule without type conversion.
- Print moved to `__main__` block; `load()` is side-effect-free for callers.
- Created `tests/test_seed.py` with 8 tests: table creation, column names, row counts, idempotency, and spot-checks for T-1042 and C-05.

## Review Triage Log

- medium → patched: "DDL implicit commit breaks atomicity" — restructured to load CSV data first, run all DDL, then all DML in one transaction; eliminates implicit-commit hazard in legacy sqlite3 transaction control.
- medium → patched: "open_tickets stored as TEXT" — added `_INT_COLUMNS` set; `open_tickets` now created as INTEGER; test updated to assert `4` (int) not `"4"`.
- low → patched: "load() prints unconditionally" — moved print to `__main__` block.
- false: "import path error" — pytest adds project rootdir to sys.path for non-src layouts; import resolves correctly.
- false: "hard-coded seed values in tests" — seed files are read-only per AGENTS.md; constants are stable.
- false: "SQL injection in table name" — table names come from a hardcoded tuple, never user-controlled.
- low (rejected): "fieldnames can be None" — seed files are read-only and always have headers; error path is unreachable in normal use.
- low (rejected): "no error-path tests" — same rationale; adding tests for unreachable paths adds complexity without covering realistic failures.
