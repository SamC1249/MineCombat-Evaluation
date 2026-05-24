"""Policy abstraction for custom agents (eval-first; works with run_eval --policy)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Action


class Policy(ABC):
    """Stateful policy: optional reset per episode, then act each tick."""

    def reset(self, ctx: dict[str, Any]) -> None:
        """Called once at episode start (scenario_id, seed, etc.)."""

    @abstractmethod
    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        """Return control for this tick."""
