# Epic 1 Context: triage data and schema

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Before the triage agent (Epic 2) can run or the eval (Epic 3) can score anything, there must be a stable, testable shape for what a triage decision *is* and a live SQLite database seeded with sample tickets and customers. Epic 1 delivers both: a rejection-enforcing schema and an idempotent seed loader. Nothing here makes network calls or requires API keys.

## Stories

- Story 1.1: The triage decision schema
- Story 1.2: The seed loader

## Requirements & Constraints

- A valid triage decision is a JSON object with exactly four fields: `category` (billing | bug | access | performance | how-to), `priority` (P1 | P2 | P3 | P4), `route` (billing-team | bug-team | access-team | performance-team | how-to-team), and `rationale` (one-sentence string). Any object with a missing field, extra field, or out-of-range value must be rejected with a clear error.
- `uv run python load_seed.py` must read `seed/tickets.csv` and `seed/customers.csv` and write them into `app.db` as tables `tickets` and `customers` with columns matching the CSV headers exactly. Running the command twice must leave `app.db` in the same state (idempotent).
- `seed/` files are read-only — the loader reads them; it never writes or modifies them.
- No network calls and no API keys anywhere in this epic.
- `mcp/triage_server.py` (read-only) already queries `app.db`: `tickets` by `ticket_id, customer_id, created_at, text`; `customers` by `customer_id, name, plan, open_tickets`. Table names and column names must stay compatible with those queries.

## Technical Decisions

- Schema validation is local-only. Pydantic is available in the project's dependencies and is the idiomatic choice, but the constraint is rejection behavior, not the library.
- SQLite via `app.db` in the project root. The loader must be idempotent — use `INSERT OR REPLACE` or equivalent upsert semantics rather than a plain insert that would duplicate rows on re-run.
- Python 3.12+, managed with uv. No pip.

## Cross-Story Dependencies

Story 1.2 (seed loader) writes data that the Epic 2 agent's MCP tools will read; its column names are load-bearing from day one. Story 1.1's schema is the shared contract that Epic 2's structured output and Epic 3's eval both validate against — it must be stable before Story 1.2 ships.
