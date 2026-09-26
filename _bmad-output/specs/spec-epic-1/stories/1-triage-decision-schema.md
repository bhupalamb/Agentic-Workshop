---
title: 'The triage decision schema'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '_bmad-output/specs/spec-epic-1/SPEC.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no validated shape for a triage decision. Epic 2's agent needs a schema to return structured output against, and Epic 3's eval needs one to score against; without it neither can be built or tested.

**Approach:** Implement a Pydantic v2 model `TriageDecision` in `schema.py` with four validated fields (category, priority, route, rationale). Any object that does not conform is rejected with a clear `ValidationError`. Add `tests/test_schema.py` covering valid decisions and each failure mode.

</frozen-after-approval>

## Implementation Notes

- Created `schema.py` with `TriageDecision` Pydantic v2 model; added `extra="forbid"` to reject unknown fields and `min_length=1` on `rationale` to enforce non-empty.
- Created `tests/test_schema.py` with 10 tests covering all enum values, missing field, extra field, and empty rationale.
- Blind-hunter review: category/route cross-field consistency finding marked false (SPEC.md assumptions explicitly scope it out as policy logic); empty rationale and missing test coverage patched; top-level module structure deferred.

## Review Triage Log

- false: "No enforcement that category and route are consistent" — SPEC.md assumptions section explicitly documents this as out of scope; cross-field pairing is policy logic for the Epic 2 agent, not schema-level validation.
- medium → patched: "rationale has no length constraint" — added `min_length=1` via `Field`; empty string is not a valid one-sentence rationale.
- medium → patched: "No test for empty rationale" — added `test_empty_rationale_rejected`.
- low → patched: "test_valid_decision doesn't assert rationale" — added assertion.
- false: "No test for category/route mismatch" — same root cause as first finding; out of scope.
- defer: "schema.py is a top-level module" — consistent with existing project structure; logged in deferred-work.md.
- low → rejected: "tests/__init__.py is empty" — harmless, pytest doesn't need it; not worth a change.

## Review Findings

> Generated: 2026-09-26 | Branch: story/bhaskar-1.1 | Reviewer: bmad-code-review

### Patch

- [ ] [Review][Patch] Loop tests make no assertions — `test_all_categories`, `test_all_priorities`, `test_all_routes` construct objects but never assert the stored field value; a coercion regression would pass silently [tests/test_schema.py:22-31]
- [ ] [Review][Patch] Missing-field coverage only for rationale — `test_missing_field` only omits `rationale`; `category`, `priority`, and `route` are not tested for missing-field rejection [tests/test_schema.py:47]
- [ ] [Review][Patch] Whitespace-only rationale passes validation — `' '` (single space) satisfies `min_length=1` and is accepted; verified with live run; fix: `Field(min_length=1, pattern=r'\S')` [schema.py:14]

### Defer

- [x] [Review][Defer] `rationale` one-sentence enforcement has no upper bound [schema.py:14] — deferred: spec says "one-sentence" but specifies no `max_length`; implementation deliberately chose `min_length=1` for "non-empty"; requires spec clarification to mandate a machine-checkable sentence constraint
- [x] [Review][Defer] `deferred-work.md` lacks a resolution trigger for the schema module location [_bmad-output/implementation-artifacts/deferred-work.md] — deferred: pre-existing planning artifact; no "done when" condition; no code impact until Epic 2 import chain is established
- [x] [Review][Defer] `stories.yaml` IDs use bare integers instead of dotted story slugs [_bmad-output/specs/spec-epic-1/stories.yaml] — deferred: planning artifact convention; no functional impact on code or tooling

### Rejected

- **false** — `test_extra_field_rejected` uses keyword arg, not dict-spread: both call forms are functionally identical in Python/Pydantic v2; verified with live run — both raise `ValidationError`
- **false** — No `__repr__` or documented serialization contract: Pydantic v2 `BaseModel` provides `__repr__`, `model_dump()`, and `model_dump_json()` with well-defined behavior out of the box
- **false** — No test for `None`/non-string values: Pydantic v2 enforces Python types automatically and deterministically; the claimed harm ("no documented expectation") names no concrete failure mode
- **false** — Diff adds spec files outside story scope: `_bmad-output/specs/spec-epic-1/` artifacts are the expected output of the `bmad-spec` workflow, not a story scope violation
- **false** — No `pyproject.toml` change for pydantic: `pydantic>=2.8` is already explicitly declared in `pyproject.toml`
- **low (rejected)** — `ATTENDEES.md` lacks last name: cosmetic documentation issue with no code or developer impact in everyday use
