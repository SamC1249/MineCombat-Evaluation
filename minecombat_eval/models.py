"""Wire types for protocol v1 (MVP0)."""

from __future__ import annotations

from dataclasses import dataclass


PROTOCOL_VERSION = 1


@dataclass
class Action:
    forward: float = 0.0
    strafe: float = 0.0
    yaw_delta: float = 0.0
    pitch_delta: float = 0.0
    jump: bool = False
    attack: bool = False
    sprint: bool = False
    hotbar_slot: int = 0

    def to_wire(self) -> dict[str, object]:
        return {
            "forward": self.forward,
            "strafe": self.strafe,
            "yaw_delta": self.yaw_delta,
            "pitch_delta": self.pitch_delta,
            "jump": self.jump,
            "attack": self.attack,
            "sprint": self.sprint,
            "hotbar_slot": self.hotbar_slot,
        }


@dataclass
class EpisodeResult:
    """One finished episode for JSONL logging."""

    scenario_id: str
    seed: int
    episode_id: str
    outcome: str | None
    reason: str | None
    ticks: int
    truncated: bool
    protocol: int
    plugin_version: str | None
    paper_minecraft: str | None
    scenario_version: str | None = None
    scenario_level: int | None = None
    task_spec: dict[str, object] | None = None
    suite_id: str | None = None
    task_id: str | None = None
    skill_family: str | None = None

    def to_json_obj(self) -> dict[str, object]:
        d: dict[str, object] = {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "episode_id": self.episode_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "ticks": self.ticks,
            "truncated": self.truncated,
            "protocol": self.protocol,
            "plugin_version": self.plugin_version,
            "paper_minecraft": self.paper_minecraft,
        }
        if self.scenario_version is not None:
            d["scenario_version"] = self.scenario_version
        if self.scenario_level is not None:
            d["scenario_level"] = self.scenario_level
        if self.task_spec is not None:
            d["task_spec"] = self.task_spec
        if self.suite_id is not None:
            d["suite_id"] = self.suite_id
        if self.task_id is not None:
            d["task_id"] = self.task_id
        if self.skill_family is not None:
            d["skill_family"] = self.skill_family
        return d
