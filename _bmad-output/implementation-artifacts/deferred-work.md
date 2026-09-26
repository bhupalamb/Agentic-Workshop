- source_spec: `_bmad-output/specs/spec-epic-1/stories/1-triage-decision-schema.md`
  summary: Move schema.py into a package (e.g. src/triage_agent/schema.py) to avoid top-level module shadowing.
  evidence: schema.py is a bare top-level module consistent with the existing project structure (run_agent.py, mcp/triage_server.py), but the import `from schema import TriageDecision` is fragile and could shadow an installed `schema` package as the project grows.

## Deferred from: code review of 1-triage-decision-schema (2026-09-26)

- `rationale` one-sentence enforcement has no upper bound — spec says "one-sentence" but specifies no `max_length`; implementation deliberately chose `min_length=1` for "non-empty"; requires spec update to mandate a machine-checkable sentence constraint if stricter validation is needed in Epic 2/3.
- `deferred-work.md` lacks a resolution trigger for the schema module location — no "done when" condition or prerequisite link; should be linked to an Epic 2 story once the import chain is established.
- `stories.yaml` IDs use bare integers (`"1"`, `"2"`) instead of dotted story slugs (`"1.1"`, `"1.2"`) — planning artifact convention inconsistency; no functional impact on code or tooling.

- source_spec: `_bmad-output/specs/spec-epic-2/stories/1-the-triage-agent.md`
  summary: _load_policy() at import time raises FileNotFoundError; run_agent.py catches only ImportError so the helpful startup message is bypassed.
  evidence: TRIAGE_POLICY.md is a read-only project file and its presence is a deployment invariant; _load_policy() now raises RuntimeError (from OSError) which surfaceswith a clear message at import. The run_agent.py guard message is a pre-existing limitation outside this story's scope.

- source_spec: `_bmad-output/specs/spec-epic-2/stories/2-human-gated-escalation.md`
  summary: Non-ValidationError/RuntimeError exceptions (e.g. network timeout) bypass the retry loop in triage().
  evidence: Pre-existing from Story 2.1 design; inherited by Story 2.2 without change. Would require broadening the except clauses.
- source_spec: `_bmad-output/specs/spec-epic-2/stories/2-human-gated-escalation.md`
  summary: 'no' answer to escalation prompt does not explicitly verify LLM won't produce escalated output afterward.
  evidence: Relies entirely on middleware sending a clear rejection signal to the LLM; speculative risk only verifiable with live middleware testing.
