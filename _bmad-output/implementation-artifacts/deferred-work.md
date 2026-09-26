- source_spec: `_bmad-output/specs/spec-epic-1/stories/1-triage-decision-schema.md`
  summary: Move schema.py into a package (e.g. src/triage_agent/schema.py) to avoid top-level module shadowing.
  evidence: schema.py is a bare top-level module consistent with the existing project structure (run_agent.py, mcp/triage_server.py), but the import `from schema import TriageDecision` is fragile and could shadow an installed `schema` package as the project grows.
