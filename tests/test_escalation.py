"""Tests for CAP-5: human-gated escalation via HumanInTheLoopMiddleware.

All tests use monkeypatching to avoid real API or subprocess calls.
The HITL pattern works by having agent.ainvoke() return a dict containing
'__interrupt__' when escalation is requested. _run_with_hitl detects this,
prompts the user, and calls ainvoke() again with a Command(resume=...).
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from schema import TriageDecision


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

P1_ENTERPRISE_DECISION = TriageDecision(
    category="bug",
    priority="P1",
    route="bug-team",
    rationale="Critical outage for Enterprise customer.",
)

P2_BILLING_DECISION = TriageDecision(
    category="billing",
    priority="P2",
    route="billing-team",
    rationale="Customer billed incorrectly.",
)

# Simulated interrupt payload the middleware would attach
_INTERRUPT_PAYLOAD = [{"type": "tool_call", "tool_name": "escalate_to_human"}]


def _make_fake_hitl_agent(
    first_result: dict,
    resume_result: dict | None = None,
):
    """Return a fake agent that simulates the HITL interrupt cycle.

    *first_result* is returned on the first ainvoke call.
    *resume_result* is returned on the second ainvoke call (after Command resume).
    If *resume_result* is None the second call is never expected.
    """
    call_count = 0

    async def fake_ainvoke(input_: Any, **kwargs: Any) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return first_result
        # Second call: resume after interrupt
        assert resume_result is not None, "Unexpected second ainvoke call"
        return resume_result

    fake = MagicMock()
    fake.ainvoke = fake_ainvoke
    return fake


def _make_fake_mcp_client(tools: list = None):
    """Return a fake MultiServerMCPClient whose get_tools() returns *tools*."""
    tools = tools or []
    fake_client = MagicMock()
    fake_client.get_tools = AsyncMock(return_value=tools)
    return fake_client


# ---------------------------------------------------------------------------
# Test: escalation triggered + approved (user says "yes")
# ---------------------------------------------------------------------------


class TestEscalationApproved:
    """When a P1/Enterprise ticket fires and the user answers 'yes', the run
    completes with the escalated decision recorded."""

    def test_yes_completes_run_as_escalated(self, monkeypatch):
        import agent as agent_module

        # First ainvoke returns an interrupt; second returns the final decision.
        interrupted = {"__interrupt__": _INTERRUPT_PAYLOAD}
        final = {"structured_response": P1_ENTERPRISE_DECISION}
        fake_agent = _make_fake_hitl_agent(
            first_result=interrupted,
            resume_result=final,
        )

        # Simulate user typing "yes"
        monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            result = asyncio.run(agent_module.triage("T-escalate-yes"))

        assert result["priority"] == "P1"
        assert result["category"] == "bug"

    def test_yes_resumes_with_approve_command(self, monkeypatch):
        """Verify the Command passed on resume contains type='approve' and the
        correct config (thread_id) is forwarded to the second ainvoke call."""
        import agent as agent_module
        from langgraph.types import Command

        ticket_id = "T-escalate-approve-check"
        captured_resume_input = {}

        async def fake_ainvoke(input_: Any, **kwargs: Any) -> dict:
            if isinstance(input_, dict):
                return {"__interrupt__": _INTERRUPT_PAYLOAD}
            # input_ is a Command on the second (resume) call — capture everything
            captured_resume_input["command"] = input_
            captured_resume_input["kwargs"] = kwargs
            return {"structured_response": P1_ENTERPRISE_DECISION}

        fake_agent = MagicMock()
        fake_agent.ainvoke = fake_ainvoke

        monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            asyncio.run(agent_module.triage(ticket_id))

        cmd = captured_resume_input.get("command")
        assert isinstance(cmd, Command)
        decisions = cmd.resume["decisions"]
        assert len(decisions) == 1
        assert decisions[0]["type"] == "approve"
        # config must be forwarded so HITL state is preserved across the resume call
        assert captured_resume_input["kwargs"].get("config") == {
            "configurable": {"thread_id": ticket_id}
        }


# ---------------------------------------------------------------------------
# Test: escalation triggered + declined (user says "no")
# ---------------------------------------------------------------------------


class TestEscalationDeclined:
    """When a P1/Enterprise ticket fires and the user answers 'no', the run
    completes without escalating."""

    def test_no_completes_run_without_escalating(self, monkeypatch):
        import agent as agent_module

        interrupted = {"__interrupt__": _INTERRUPT_PAYLOAD}
        # After rejection the agent can still return a valid (non-escalated) decision
        final = {"structured_response": P2_BILLING_DECISION}
        fake_agent = _make_fake_hitl_agent(
            first_result=interrupted,
            resume_result=final,
        )

        monkeypatch.setattr("builtins.input", lambda _prompt: "no")

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            result = asyncio.run(agent_module.triage("T-escalate-no"))

        # Decision came back without escalation
        assert result["priority"] == "P2"
        assert result["category"] == "billing"

    def test_no_resumes_with_reject_command(self, monkeypatch):
        """Verify the Command passed on resume contains type='reject' and the
        correct config (thread_id) is forwarded to the second ainvoke call."""
        import agent as agent_module
        from langgraph.types import Command

        ticket_id = "T-escalate-reject-check"
        captured_resume_input = {}

        async def fake_ainvoke(input_: Any, **kwargs: Any) -> dict:
            if isinstance(input_, dict):
                return {"__interrupt__": _INTERRUPT_PAYLOAD}
            # input_ is a Command on the second (resume) call — capture everything
            captured_resume_input["command"] = input_
            captured_resume_input["kwargs"] = kwargs
            return {"structured_response": P2_BILLING_DECISION}

        fake_agent = MagicMock()
        fake_agent.ainvoke = fake_ainvoke

        monkeypatch.setattr("builtins.input", lambda _prompt: "no")

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            asyncio.run(agent_module.triage(ticket_id))

        cmd = captured_resume_input.get("command")
        assert isinstance(cmd, Command)
        decisions = cmd.resume["decisions"]
        assert len(decisions) == 1
        assert decisions[0]["type"] == "reject"
        # config must be forwarded so HITL state is preserved across the resume call
        assert captured_resume_input["kwargs"].get("config") == {
            "configurable": {"thread_id": ticket_id}
        }


# ---------------------------------------------------------------------------
# Test: no escalation triggered (non-P1 or non-Enterprise)
# ---------------------------------------------------------------------------


class TestNoEscalationTriggered:
    """When no escalation rule fires, no interrupt occurs and no prompt appears."""

    def test_no_interrupt_means_no_prompt(self, monkeypatch):
        """If __interrupt__ is absent the input() builtin must never be called."""
        import agent as agent_module

        # input() will raise if called, proving no prompt was issued
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: (_ for _ in ()).throw(
                AssertionError("input() called unexpectedly — no escalation should occur")
            ),
        )

        # Direct result with no interrupt
        final = {"structured_response": P2_BILLING_DECISION}
        fake_agent = _make_fake_hitl_agent(first_result=final)

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            result = asyncio.run(agent_module.triage("T-1042"))

        assert result["priority"] == "P2"

    def test_no_interrupt_calls_ainvoke_once(self, monkeypatch):
        """Without an interrupt, ainvoke is called exactly once."""
        import agent as agent_module

        call_count = {"n": 0}

        async def counting_ainvoke(input_: Any, **kwargs: Any) -> dict:
            call_count["n"] += 1
            return {"structured_response": P2_BILLING_DECISION}

        fake_agent = MagicMock()
        fake_agent.ainvoke = counting_ainvoke

        monkeypatch.setattr("builtins.input", lambda _prompt: "yes")  # should not be reached

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", return_value=fake_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            asyncio.run(agent_module.triage("T-no-escalation"))

        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Test: escalate_to_human tool is registered with the agent
# ---------------------------------------------------------------------------


class TestEscalateToolRegistered:
    """The escalate_to_human tool must appear in the tools list given to create_agent."""

    def test_escalate_tool_in_tools_list(self, monkeypatch):
        import agent as agent_module

        captured = {}

        def fake_create_agent(**kwargs):
            captured["tools"] = kwargs.get("tools", [])
            fake = MagicMock()
            fake.ainvoke = AsyncMock(
                return_value={"structured_response": P2_BILLING_DECISION}
            )
            return fake

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", side_effect=fake_create_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            asyncio.run(agent_module.triage("T-tool-check"))

        tool_names = [t.name for t in captured["tools"]]
        assert "escalate_to_human" in tool_names, (
            f"escalate_to_human not found in tools: {tool_names}"
        )

    def test_hitl_middleware_wired_to_create_agent(self, monkeypatch):
        """create_agent must be called with HumanInTheLoopMiddleware in middleware."""
        import agent as agent_module
        from langchain.agents.middleware import HumanInTheLoopMiddleware

        captured = {}

        def fake_create_agent(**kwargs):
            captured["middleware"] = kwargs.get("middleware", [])
            fake = MagicMock()
            fake.ainvoke = AsyncMock(
                return_value={"structured_response": P2_BILLING_DECISION}
            )
            return fake

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", side_effect=fake_create_agent),
            patch.object(agent_module, "MemorySaver", return_value=MagicMock()),
        ):
            asyncio.run(agent_module.triage("T-middleware-check"))

        middleware_types = [type(m) for m in captured["middleware"]]
        assert HumanInTheLoopMiddleware in middleware_types, (
            f"HumanInTheLoopMiddleware not found in middleware: {middleware_types}"
        )

    def test_memorysaver_checkpointer_used(self, monkeypatch):
        """create_agent must be called with a MemorySaver checkpointer."""
        import agent as agent_module
        from langgraph.checkpoint.memory import MemorySaver

        captured = {}
        fake_saver = MemorySaver()

        def fake_create_agent(**kwargs):
            captured["checkpointer"] = kwargs.get("checkpointer")
            fake = MagicMock()
            fake.ainvoke = AsyncMock(
                return_value={"structured_response": P2_BILLING_DECISION}
            )
            return fake

        with (
            patch.object(agent_module, "_make_llm", return_value=MagicMock()),
            patch.object(
                agent_module,
                "MultiServerMCPClient",
                return_value=_make_fake_mcp_client(),
            ),
            patch.object(agent_module, "create_agent", side_effect=fake_create_agent),
            patch.object(agent_module, "MemorySaver", return_value=fake_saver),
        ):
            asyncio.run(agent_module.triage("T-checkpointer-check"))

        assert captured["checkpointer"] is fake_saver
