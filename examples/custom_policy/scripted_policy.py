"""Scripted policy: a fixed action sequence that ignores the observation.

Smallest possible policy. Good first run to confirm the eval loop works
end to end before you add any decision logic.

    minecombat-eval test-policy examples.custom_policy.scripted_policy:ScriptedPolicy
"""

from __future__ import annotations

from typing import Any

from minecombat_eval import Action, Policy


class ScriptedPolicy(Policy):
    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        # Walk forward and swing on even ticks. Swap in your own scripted plan.
        return Action(forward=1.0, attack=(tick % 2 == 0))
