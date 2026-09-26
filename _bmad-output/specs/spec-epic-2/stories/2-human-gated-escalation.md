---
title: 'Human-gated escalation'
type: 'feature'
created: '2026-09-26'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '_bmad-output/specs/spec-epic-2/SPEC.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The escalation policy (P1 + Enterprise customer) must never fire automatically — a person must approve it first. There is currently no `escalate_to_human` tool or human-in-the-loop approval gate, so any agent would either skip escalation entirely or escalate without pausing for consent.

**Approach:** Add an `escalate_to_human` tool to `agent.py` and wire it through LangChain's human-in-the-loop middleware so a terminal yes/no prompt fires before any escalation executes. "yes" completes the run as escalated; "no" completes the run without escalating.

## Boundaries & Constraints

**Always:**
- `escalate_to_human` is a locally-defined tool — it cannot live in `mcp/triage_server.py` (read-only).
- The tool must be gated end-to-end by LangChain's human-in-the-loop middleware (approval required before execution).
- A "no" answer must result in a normal completed run with no escalation.
- A "yes" answer must result in the escalation completing.
- Escalation must never fire automatically.
- **Scope decision (Option A):** This story adds only CAP-5 to an `agent.py` already created by Story 2.1. Implementation cannot begin until `agent.py` exists on this branch with a working `triage()` function.

**Never:**
- Modify `mcp/triage_server.py`, `schema.py`, `TRIAGE_POLICY.md`, or anything under `seed/`.
- Implement automatic escalation that bypasses the human approval gate.
- Add escalation logic inside the MCP server.
- Implement Story 2.1 capabilities (CAP-1 through CAP-4, CAP-6) as part of this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Escalation approved | Ticket → P1 + Enterprise customer; user answers "yes" | Run completes, escalation recorded in trace | N/A |
| Escalation declined | Ticket → P1 + Enterprise customer; user answers "no" | Run completes without escalating, decision returned normally | N/A |
| No escalation triggered | Ticket → not P1, or non-Enterprise customer | No human prompt; decision returned directly | N/A |

</frozen-after-approval>

## Code Map

- `agent.py` — does not exist yet; must be created by Story 2.1 (option A) or within this spec (option B). Will contain the `triage(ticket_id: str)` async function imported by `run_agent.py`, the MCP tool setup, the provider switch, structured-output loop, and (once this story's scope is resolved) `escalate_to_human` plus the middleware wiring.
- `run_agent.py` — existing stub; protected MLflow lines (`sqlite:///mlflow.db`, experiment `triage-agent`, `mlflow.langchain.autolog()`); imports `triage` from `agent` and calls it with `asyncio.run`. Not modified by this story.
- `schema.py` — provides `TriageDecision` (done, read-only); the agent's structured output validates against it.
- `mcp/triage_server.py` — provides `get_ticket` and `get_customer_history` over stdio (read-only). Tools are loaded via `langchain-mcp-adapters`.
- `TRIAGE_POLICY.md` — defines the escalation rule (P1 + Enterprise → call `escalate_to_human`), priority/category/route tables, the Enterprise bump rule (3+ open tickets → priority up one level), and the Safety section. Agent system prompt must encode this.
- `pyproject.toml` — `langchain-mcp-adapters`, `langchain-google-genai`, `langchain-groq` already declared; no new dependencies expected for the human-in-the-loop gate.
- `.claude/skills/langchain-middleware` — project skill covering `HumanInTheLoopMiddleware`, the `Command`/interrupt resume pattern, and structured output; load before implementing.

## Tasks & Acceptance

**Execution:**
- [ ] `agent.py` — add `escalate_to_human(ticket_id: str) -> str` tool function (a no-op stub that returns a confirmation string; the middleware handles the actual pause); register it alongside the MCP tools in the agent's tool list
- [ ] `agent.py` — wrap `escalate_to_human` with `HumanInTheLoopMiddleware` (from `langchain-middleware` skill) so the agent pauses for a terminal yes/no before the tool executes; "no" must result in the tool call being declined and the run completing without escalation
- [ ] `tests/test_escalation.py` — add tests using monkeypatched stdin/approval callback covering: escalation triggered + approved, escalation triggered + declined, escalation not triggered (no prompt fires)

**Acceptance Criteria:**
- Given a ticket that resolves to P1 with an Enterprise customer, when the agent runs, then `run_agent.py` pauses at the terminal with a yes/no prompt before any escalation executes.
- Given the user answers "yes", when the prompt resolves, then the run completes with escalation recorded in the MLflow trace.
- Given the user answers "no", when the prompt resolves, then the run completes without escalating and returns a normal `TriageDecision`.
- Given any ticket that does not trigger the escalation rule (not P1, or not Enterprise), when the agent runs, then no human prompt appears.
- Given any scenario, when the run completes, then escalation has never fired without an explicit "yes".

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

The LangChain human-in-the-loop approval pattern is covered by the `langchain-middleware` skill in this project. It documents `HumanInTheLoopMiddleware` for tool-call approval, the `Command` resume pattern, and structured output with Pydantic. Load that skill before implementing — do not derive the middleware wiring from first principles.

## Verification

**Commands:**
- `uv run pytest` — expected: all tests pass
- `uv run python run_agent.py <P1-Enterprise-ticket-id>` — expected: terminal pauses for yes/no; "yes" completes as escalated; "no" completes without escalating; no prompt fires for non-escalation tickets
