---
id: SPEC-epic-1
companions: [../../../mcp/triage_server.py]
sources: [../../../INTENT.md]
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 1: triage data and schema

## Why

The workshop needs a validated decision schema and a seeded local database before any agent can triage tickets. This epic delivers both: a rejection-enforcing schema and an idempotent loader that populates `app.db` from the read-only seed files.

## Capabilities

- **CAP-1**
  - **intent:** Every triage decision is a validated JSON object. Objects that don't conform are rejected with a clear error.
  - **success:** A decision with `category` ∈ {billing, bug, access, performance, how-to}, `priority` ∈ {P1, P2, P3, P4}, `route` ∈ {billing-team, bug-team, access-team, performance-team, how-to-team}, and a one-sentence `rationale` passes validation. Any object with a missing field, an extra field, or an out-of-range value raises a clear error.

- **CAP-2**
  - **intent:** One command loads `seed/tickets.csv` and `seed/customers.csv` into a local SQLite file `app.db` as tables `tickets` and `customers`, with the same columns as the CSVs. Running it twice gives the same database.
  - **success:** `uv run python load_seed.py` creates `app.db` with tables `tickets` and `customers` whose columns match the CSV headers exactly. Running the command a second time produces an identical database (idempotent).

## Constraints

- Python 3.12 or newer, managed with uv. No pip.
- `seed/` files are read-only — the loader reads them; it never writes or modifies them.
- No network calls and no API keys in this epic.
- Table names (`tickets`, `customers`) and column names in `app.db` must remain compatible with `mcp/triage_server.py`, which already reads them.

## Non-goals

- The LangChain agent, MCP tools, eval harness, and any user interface.

## Success signal

`uv run python load_seed.py` completes without error and `app.db` contains `tickets` and `customers` tables with columns matching the seed CSVs. A decision object for ticket T-1042 — `{"category": "billing", "priority": "P2", "route": "billing-team", "rationale": "..."}` — passes CAP-1 validation; an object with `"priority": "P5"` is rejected with a clear error.
