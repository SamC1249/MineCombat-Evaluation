"""Typed helpers for writing policies (targeting, aiming, action checks).

Pure, stdlib-only functions that remove the boilerplate of mapping a v1
observation (see ``planning/observation-v1.md``) to an :class:`Action`. Safe to
import in offline tests; nothing here touches the network.

Typical use inside ``Policy.act``::

    from minecombat_eval import nearest_mob, aim_at, Action

    target = nearest_mob(observation)
    if target is None:
        return Action()
    yaw_delta, pitch_delta = aim_at(observation["player"], target)
    dist = target["distance"]
    return Action(forward=1.0 if dist > 3 else 0.0,
                  yaw_delta=yaw_delta, pitch_delta=pitch_delta,
                  attack=dist <= 3.2)
"""

from __future__ import annotations

import math
from typing import Any

from .models import Action

Mob = dict[str, Any]
Observation = dict[str, Any]

# Per-tick look limits used by the reference baseline; reasonable defaults for
# any heuristic. Override via aim_at(...) keyword args if your policy differs.
DEFAULT_MAX_YAW_STEP = 15.0
DEFAULT_MAX_PITCH_STEP = 8.0


def clamp(value: float, lo: float, hi: float) -> float:
    """Constrain ``value`` to the inclusive ``[lo, hi]`` range."""
    return max(lo, min(hi, value))


def normalize_yaw(delta: float) -> float:
    """Wrap a yaw difference into ``[-180, 180]`` so you turn the short way."""
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return delta


def mobs(observation: Observation | None) -> list[Mob]:
    """Return the hostile list from an observation (``[]`` if missing/malformed)."""
    if not isinstance(observation, dict):
        return []
    value = observation.get("mobs")
    if not isinstance(value, list):
        return []
    return [m for m in value if isinstance(m, dict)]


def mob_distance(observation: Observation | None, mob: Mob) -> float | None:
    """Distance from player to ``mob``.

    Uses the server-provided ``distance`` field when present, otherwise computes
    it from player/mob positions. Returns ``None`` if neither is available.
    """
    d = mob.get("distance")
    if isinstance(d, (int, float)):
        return float(d)
    player = (observation or {}).get("player") if isinstance(observation, dict) else None
    if not isinstance(player, dict):
        return None
    try:
        dx = float(mob["x"]) - float(player["x"])
        dy = float(mob["y"]) - float(player["y"])
        dz = float(mob["z"]) - float(player["z"])
    except (KeyError, TypeError, ValueError):
        return None
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def mobs_by_distance(observation: Observation | None) -> list[Mob]:
    """Hostiles sorted nearest-first; entries with no known distance go last."""
    inf = float("inf")
    return sorted(
        mobs(observation),
        key=lambda m: (mob_distance(observation, m) if mob_distance(observation, m) is not None else inf),
    )


def nearest_mob(observation: Observation | None) -> Mob | None:
    """The closest hostile, or ``None`` if no mobs are visible."""
    ranked = mobs_by_distance(observation)
    return ranked[0] if ranked else None


def aim_at(
    player: dict[str, Any],
    target: dict[str, Any],
    *,
    max_yaw_step: float = DEFAULT_MAX_YAW_STEP,
    max_pitch_step: float = DEFAULT_MAX_PITCH_STEP,
    target_height: float = 0.0,
) -> tuple[float, float]:
    """Clamped ``(yaw_delta, pitch_delta)`` that turns ``player`` toward ``target``.

    ``player`` needs ``x, y, z`` and optionally ``yaw, pitch``. ``target`` needs
    ``x, y, z``. ``target_height`` raises the aim point above the target's feet
    (e.g. ~1.4 to aim at a humanoid's head). Returns ``(0.0, 0.0)`` if positions
    are missing so callers can pass it straight into :class:`Action`.
    """
    try:
        px, py, pz = float(player["x"]), float(player["y"]), float(player["z"])
        tx, ty, tz = float(target["x"]), float(target["y"]), float(target["z"])
    except (KeyError, TypeError, ValueError):
        return 0.0, 0.0
    yaw = float(player.get("yaw", 0.0))
    pitch = float(player.get("pitch", 0.0))

    dx, dy, dz = tx - px, (ty + target_height) - py, tz - pz
    horiz = math.hypot(dx, dz)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    target_pitch = -math.degrees(math.atan2(dy, horiz)) if horiz > 1e-6 else pitch

    yaw_delta = clamp(normalize_yaw(target_yaw - yaw), -max_yaw_step, max_yaw_step)
    pitch_delta = clamp(target_pitch - pitch, -max_pitch_step, max_pitch_step)
    return yaw_delta, pitch_delta


def player_health_fraction(observation: Observation | None) -> float | None:
    """Player HP as a fraction of max (``0.0``–``1.0``), or ``None`` if unknown."""
    if not isinstance(observation, dict):
        return None
    player = observation.get("player")
    if not isinstance(player, dict):
        return None
    try:
        health = float(player["health"])
        max_health = float(player.get("max_health", 20.0))
    except (KeyError, TypeError, ValueError):
        return None
    if max_health <= 0.0:
        return None
    return clamp(health / max_health, 0.0, 1.0)


# Bounds the server accepts for movement axes; outside this the value is clamped
# server-side, which usually means a policy bug rather than intent.
_AXIS_RANGE = (-1.0, 1.0)
_HOTBAR_RANGE = (0, 8)


def validate_action(action: Any) -> list[str]:
    """Check an action's shape/ranges. Returns a list of problems (``[]`` = ok).

    Used by ``minecombat-eval test-policy`` to catch common mistakes before a
    live run: non-:class:`Action` returns, NaN/inf deltas, out-of-range axes.
    """
    problems: list[str] = []
    if not isinstance(action, Action):
        return [f"act() returned {type(action).__name__}, expected Action"]

    for name in ("forward", "strafe"):
        v = getattr(action, name)
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            problems.append(f"{name}={v!r} is not a finite number")
        elif not (_AXIS_RANGE[0] <= v <= _AXIS_RANGE[1]):
            problems.append(f"{name}={v} out of range [-1.0, 1.0] (server will clamp)")

    for name in ("yaw_delta", "pitch_delta"):
        v = getattr(action, name)
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            problems.append(f"{name}={v!r} is not a finite number")

    slot = action.hotbar_slot
    if not isinstance(slot, int) or not (_HOTBAR_RANGE[0] <= slot <= _HOTBAR_RANGE[1]):
        problems.append(f"hotbar_slot={slot!r} out of range [0, 8]")

    for name in ("jump", "attack", "sprint"):
        v = getattr(action, name)
        if not isinstance(v, bool):
            problems.append(f"{name}={v!r} should be a bool")

    return problems
