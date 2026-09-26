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
