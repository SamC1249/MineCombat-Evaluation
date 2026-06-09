"""Conditional heuristic policy built from the minecombat_eval helpers.

Targets the nearest hostile, aims with clamped look deltas, closes distance,
and attacks in melee range. This is the pattern most hand-written agents use.

    minecombat-eval test-policy examples.custom_policy.conditional_policy:ConditionalPolicy
"""

from __future__ import annotations

from typing import Any

from minecombat_eval import Action, Policy, aim_at, nearest_mob, player_health_fraction


class ConditionalPolicy(Policy):
    def reset(self, ctx: dict[str, Any]) -> None:
        # ctx has scenario_id, seed (+ suite_id/task_id in suites). Reset state here.
        self._last_strafe = 0.5

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        target = nearest_mob(observation)
        if target is None or not isinstance(observation, dict):
            return Action()

        player = observation["player"]
        dist = float(target.get("distance", 99.0))
        yaw_delta, pitch_delta = aim_at(player, target)

        # Back off and stop attacking if we are low on health.
        hp = player_health_fraction(observation) or 1.0
        if hp < 0.3:
            return Action(forward=-1.0, sprint=True, yaw_delta=yaw_delta, pitch_delta=pitch_delta)

        # Circle-strafe in melee so we are a harder target.
        strafe = 0.0
        if dist < 2.5:
            self._last_strafe = -self._last_strafe if tick % 20 == 0 else self._last_strafe
            strafe = self._last_strafe

        return Action(
            forward=1.0 if dist > 3.0 else 0.0,
            strafe=strafe,
            yaw_delta=yaw_delta,
            pitch_delta=pitch_delta,
            sprint=dist > 6.0,
            jump=bool(player.get("on_ground", True)) and dist < 2.0,
            attack=dist <= 3.2,
        )
