---
title: 'Human-gated escalation'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'dispatch'
baseline_commit: '2f19b90050644bb3b47be5de31d3faafe19c827d'
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

- `agent.py` — exists (Story 2.1). Contains `_load_policy()`, `SYSTEM_PROMPT`, `_make_llm()`, `_mcp_connections()`, `_extract()`, `async def triage(ticket_id)`. **Add:** `escalate_to_human` tool decorated with `@tool`; `_run_with_hitl()` async helper that invokes the agent, detects `__interrupt__`, prompts the user at the terminal, and resumes with `Command(resume=...)`; `HumanInTheLoopMiddleware` and `MemorySaver` checkpointer wired into `create_agent`; restructure `triage()` to use the helper and pass `config={"configurable": {"thread_id": ticket_id}}`.
- `run_agent.py` — existing; protected MLflow lines; not modified by this story.
- `schema.py` — `TriageDecision` structured output target; read-only.
- `mcp/triage_server.py` — MCP tools over stdio; read-only.
- `TRIAGE_POLICY.md` — escalation rule already embedded in `SYSTEM_PROMPT`; read-only.
- `pyproject.toml` — no new direct dependencies; `MemorySaver` and `Command` come from `langgraph`, which is already a transitive dependency.
- `.claude/skills/langchain-middleware` — covers `HumanInTheLoopMiddleware`, `interrupt_on`, `Command(resume=...)` pattern, and the `MemorySaver` + `thread_id` requirement; load before implementing.

## Tasks & Acceptance

**Execution:**
- [x] `agent.py` — add module-level `escalate_to_human` `@tool` function with a `reason: str` parameter that returns a confirmation string; include it in `tools` list passed to `create_agent`
- [x] `agent.py` — add `MemorySaver` checkpointer and `HumanInTheLoopMiddleware(interrupt_on={"escalate_to_human": {"allowed_decisions": ["approve", "reject"]}})` to `create_agent`; pass `config={"configurable": {"thread_id": ticket_id}}` to every `ainvoke` call
- [x] `agent.py` — add `async def _run_with_hitl(agent, user_message, config) -> dict` helper: invokes the agent, checks for `"__interrupt__"` in the result, prompts `input("Escalate? [yes/no]: ")` at the terminal, resumes with `Command(resume={"decisions": [{"type": "approve" if yes else "reject"}]})`, returns the final result dict
- [x] `agent.py` — replace direct `agent.ainvoke` calls in `triage()` with `_run_with_hitl`; keep the retry-once logic wrapping it
- [x] `tests/test_escalation.py` — monkeypatched tests covering: escalation triggered + approved (user says yes → run completes), escalation triggered + declined (user says no → run completes without escalating), no escalation (non-P1/non-Enterprise → no interrupt, no prompt)

**Acceptance Criteria:**
- Given a ticket that resolves to P1 with an Enterprise customer, when the agent runs, then `run_agent.py` pauses at the terminal with a yes/no prompt before any escalation executes.
- Given the user answers "yes", when the prompt resolves, then the run completes with escalation recorded in the MLflow trace.
- Given the user answers "no", when the prompt resolves, then the run completes without escalating and returns a normal `TriageDecision`.
- Given any ticket that does not trigger the escalation rule (not P1, or not Enterprise), when the agent runs, then no human prompt appears.
- Given any scenario, when the run completes, then escalation has never fired without an explicit "yes".

## Implementation Notes

## Spec Change Log


## Review Triage Log

- **medium → patched:** BH7+ECH1 — "y" mapped silently to reject; `"yes".lower()` requires exact word; changed to `if answer in ("yes", "y"):`.
- **medium → patched:** ECH8+VGap1 — resume `ainvoke` config kwarg never asserted in tests; removing `config=config` from resume call would pass all tests silently; added `kwargs["config"]` assertion in approve and reject resume tests.
- **false:** BH1+ECH3 — `if` vs `while` for interrupt loop: only one `escalate_to_human` tool in `interrupt_on`; a second interrupt is architecturally impossible.
- **false:** BH4 — retry uses same input with no corrective feedback: inherited from Story 2.1 spec; retry-once is the mandated behavior.
- **false:** BH5 — `"__interrupt__" in result` assumes dict: `create_agent` always returns a dict from `ainvoke`; framework invariant.
- **false:** BH6+ECH7 — `escalate_to_human` returns "approved" always: middleware prevents tool body execution on rejection; body only runs on approval.
- **false:** BH8 — diff header path missing leading `/`: artifact of `git diff --no-index /dev/null` formatting; actual file path in repo is correct.
- **false:** BH10 — MCP tools unprotected by middleware: `get_ticket`/`get_customer_history` are read-only lookups; HITL only required on the escalation action per spec and policy.
- **false:** ECH9 — MemorySaver at test module level: MemorySaver has no init side effects; purely in-memory.
- **false:** ECH10 — isinstance check fragile: Command is not a dict subclass.
- **false:** ECH11 — `_extract` not mocked in call_count test: fixture supplies a real TriageDecision; `_extract` succeeds without mocking.
- **false:** ECH13 — claim "escalation not recorded in MLflow": `mlflow.langchain.autolog()` captures all tool calls including `escalate_to_human`; escalation appears in the trace automatically.
- **low (rejected):** BH2+ECH4+ECH2 — blocking `input()` in async: terminal CLI by spec; AGENTS.md scopes to terminal use; fix adds complexity for a non-problem in this context.
- **low (rejected):** BH3 — MemorySaver non-persistent: workshop design choice; restart scenario out of scope.
- **low (rejected):** BH9 — no test for ValidationError+HITL combined: highly unlikely edge case; fix adds complexity.
- **low (rejected):** ECH5 — ticket_id None/non-string: unreachable with current callers (`run_agent.py` always provides `sys.argv[1]` as string).
- **low (rejected):** ECH6 — retry re-prompts on escalate+approve+_extract failure: vanishingly unlikely combined scenario.
- **low → defer:** ECH12 — non-ValidationError/RuntimeError bypass retry: pre-existing from Story 2.1 design; not caused by this story.
- **defer:** ECH14 — "no" doesn't guarantee LLM won't produce escalated output: speculative; middleware framework behavior not testable without live middleware.

## Design Notes

The LangChain human-in-the-loop approval pattern is covered by the `langchain-middleware` skill in this project. It documents `HumanInTheLoopMiddleware` for tool-call approval, the `Command` resume pattern, and structured output with Pydantic. Load that skill before implementing — do not derive the middleware wiring from first principles.

## Verification

**Commands:**
- `uv run pytest` — expected: all tests pass
- `uv run python run_agent.py <P1-Enterprise-ticket-id>` — expected: terminal pauses for yes/no; "yes" completes as escalated; "no" completes without escalating; no prompt fires for non-escalation tickets
