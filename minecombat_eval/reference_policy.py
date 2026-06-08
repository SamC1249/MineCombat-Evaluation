"""Example and baseline policies for eval and documentation."""

from __future__ import annotations

from typing import Any

from .helpers import aim_at, nearest_mob
from .models import Action
from .policy import Policy


class NoopPolicy(Policy):
    """Stand still (same as stub noop agent)."""

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        return Action()


class ReferenceCombatPolicy(Policy):
    """Minimal heuristic baseline: aim at nearest hostile, close, attack in range."""

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        target = nearest_mob(observation)
        if target is None or not isinstance(observation, dict):
            return Action()
        player = observation.get("player")
        if not isinstance(player, dict) or "distance" not in target:
            return Action()

        dist = float(target["distance"])
        yaw_delta, pitch_delta = aim_at(player, target)

        forward = 1.0 if dist > 3.0 else 0.0
        strafe = 0.0
        if dist < 2.5:
            strafe = 0.5 if (tick // 20) % 2 == 0 else -0.5
        sprint = dist > 6.0
        on_ground = bool(player.get("on_ground", True))
        jump = on_ground and dist < 2.0
        attack = dist <= 3.2

        return Action(
            forward=forward,
            strafe=strafe,
            yaw_delta=yaw_delta,
            pitch_delta=pitch_delta,
            jump=jump,
            attack=attack,
            sprint=sprint,
        )
