"""Example and baseline policies for eval and documentation."""

from __future__ import annotations

import math
from typing import Any

from .models import Action
from .policy import Policy


class NoopPolicy(Policy):
    """Stand still (same as stub noop agent)."""

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        return Action()


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _normalize_yaw(delta: float) -> float:
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return delta


def _aim_deltas(
    px: float, py: float, pz: float, yaw: float, pitch: float,
    tx: float, ty: float, tz: float,
) -> tuple[float, float]:
    dx, dy, dz = tx - px, ty - py, tz - pz
    horiz = math.hypot(dx, dz)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    target_pitch = -math.degrees(math.atan2(dy, horiz)) if horiz > 1e-6 else pitch
    yaw_delta = _clamp(_normalize_yaw(target_yaw - yaw), -15.0, 15.0)
    pitch_delta = _clamp(target_pitch - pitch, -8.0, 8.0)
    return yaw_delta, pitch_delta


class ReferenceCombatPolicy(Policy):
    """Minimal heuristic baseline: aim at nearest hostile, close, attack in range."""

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        if not observation:
            return Action()
        mobs = observation.get("mobs")
        player = observation.get("player")
        if not isinstance(mobs, list) or not mobs or not isinstance(player, dict):
            return Action()

        target = min(
            (m for m in mobs if isinstance(m, dict) and "distance" in m),
            key=lambda m: float(m["distance"]),
            default=None,
        )
        if target is None:
            return Action()

        dist = float(target["distance"])
        px, py, pz = float(player["x"]), float(player["y"]), float(player["z"])
        yaw, pitch = float(player.get("yaw", 0.0)), float(player.get("pitch", 0.0))
        tx, ty, tz = float(target["x"]), float(target["y"]), float(target["z"])
        yaw_delta, pitch_delta = _aim_deltas(px, py, pz, yaw, pitch, tx, ty, tz)

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
