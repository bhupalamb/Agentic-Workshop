- source_spec: `_bmad-output/specs/spec-epic-1/stories/1-triage-decision-schema.md`
  summary: Move schema.py into a package (e.g. src/triage_agent/schema.py) to avoid top-level module shadowing.
  evidence: schema.py is a bare top-level module consistent with the existing project structure (run_agent.py, mcp/triage_server.py), but the import `from schema import TriageDecision` is fragile and could shadow an installed `schema` package as the project grows.

## Deferred from: code review of 1-triage-decision-schema (2026-09-26)

- `rationale` one-sentence enforcement has no upper bound — spec says "one-sentence" but specifies no `max_length`; implementation deliberately chose `min_length=1` for "non-empty"; requires spec update to mandate a machine-checkable sentence constraint if stricter validation is needed in Epic 2/3.
- `deferred-work.md` lacks a resolution trigger for the schema module location — no "done when" condition or prerequisite link; should be linked to an Epic 2 story once the import chain is established.
- `stories.yaml` IDs use bare integers (`"1"`, `"2"`) instead of dotted story slugs (`"1.1"`, `"1.2"`) — planning artifact convention inconsistency; no functional impact on code or tooling.
