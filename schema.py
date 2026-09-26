"""Triage decision schema and validation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TriageDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "bug", "access", "performance", "how-to"]
    priority: Literal["P1", "P2", "P3", "P4"]
    route: Literal["billing-team", "bug-team", "access-team", "performance-team", "how-to-team"]
    rationale: str = Field(min_length=1)
