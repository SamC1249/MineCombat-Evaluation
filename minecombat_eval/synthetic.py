"""Synthetic v1 observations for testing policies without a live Minecraft server.

Used by ``minecombat-eval test-policy`` and handy in unit tests. The shapes match
``planning/observation-v1.md`` exactly, so a policy that works here sees the same
keys it will see over the wire.
"""

from __future__ import annotations

import math
from typing import Any, Iterator

Observation = dict[str, Any]


def fake_player(
    *,
    x: float = 0.0,
    y: float = -60.0,
    z: float = 0.0,
    yaw: float = 0.0,
    pitch: float = 0.0,
    health: float = 20.0,
    max_health: float = 20.0,
    food: int = 20,
    on_ground: bool = True,
) -> dict[str, Any]:
    """Build a single ``player`` object."""
    return {
        "health": health,
        "max_health": max_health,
        "food": food,
        "x": x,
        "y": y,
        "z": z,
        "yaw": yaw,
        "pitch": pitch,
        "on_ground": on_ground,
    }


def fake_mob(
    kind: str,
    *,
    x: float,
    y: float,
    z: float,
    health: float = 20.0,
    player: dict[str, Any] | None = None,
    uuid: str = "00000000-0000-0000-0000-000000000000",
) -> dict[str, Any]:
    """Build one ``mobs[]`` entry; ``distance`` is filled from ``player`` if given."""
    mob = {"kind": kind, "uuid": uuid, "x": x, "y": y, "z": z, "health": health}
    if player is not None:
        dx, dy, dz = x - player["x"], y - player["y"], z - player["z"]
        mob["distance"] = math.sqrt(dx * dx + dy * dy + dz * dz)
    return mob


def fake_observation(
    *,
    tick: int = 0,
    player: dict[str, Any] | None = None,
    mobs: list[dict[str, Any]] | None = None,
    scenario_id: str = "ZombieRoom-v0",
    scenario_level: int = 1,
    hostile_entity: str = "ZOMBIE",
) -> Observation:
    """Assemble a full v1 observation (``tick``/``player``/``mobs``/``meta``)."""
    player = player if player is not None else fake_player()
    mobs = mobs if mobs is not None else []
    return {
        "tick": tick,
        "player": player,
        "mobs": mobs,
        "meta": {
            "plugin_version": "synthetic",
            "paper_minecraft": "synthetic",
            "scenario_id": scenario_id,
            "scenario_version": "1",
            "scenario_level": scenario_level,
            "time_of_day": "day",
            "world_time": 1000,
            "hostile_entity": hostile_entity,
            "hostile_count": len(mobs),
        },
    }


def approach_episode(
    n_ticks: int = 60,
    *,
    kind: str = "ZOMBIE",
    start_distance: float = 12.0,
    close_rate: float = 0.25,
    scenario_id: str = "ZombieRoom-v0",
) -> Iterator[Observation]:
    """Yield observations of one hostile walking toward the player.

    The mob starts at ``start_distance`` and closes by ``close_rate`` blocks/tick
    (floored at melee range), so a policy is exercised across every distance
    regime it cares about: sprint-to-close, approach, and in-melee. The first
    observation has no mob (mirrors a real reset before the hostile is tracked).
    """
    player = fake_player()
    yield fake_observation(tick=0, player=player, mobs=[], scenario_id=scenario_id, hostile_entity=kind)
    for tick in range(1, max(1, n_ticks)):
        dist = max(1.0, start_distance - close_rate * tick)
        mob = fake_mob(kind, x=player["x"], y=player["y"], z=player["z"] + dist, player=player)
        yield fake_observation(
            tick=tick, player=player, mobs=[mob], scenario_id=scenario_id, hostile_entity=kind
        )
