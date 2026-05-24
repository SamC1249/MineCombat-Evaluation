"""Example policies for documentation and smoke tests."""

from __future__ import annotations

from typing import Any

from .models import Action
from .policy import Policy


class NoopPolicy(Policy):
    """Stand still (same as stub noop agent)."""

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        return Action()
