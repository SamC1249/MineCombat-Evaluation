"""Stub agents for validating eval loops (noop / random)."""

from __future__ import annotations

import random
from typing import Any, Protocol

from .models import Action


class AgentFn(Protocol):
    def __call__(self, observation: dict[str, Any] | None, tick: int) -> Action: ...


def noop_agent(_observation: dict[str, Any] | None, _tick: int) -> Action:
    return Action()


def make_random_agent(*, seed: int | None = None) -> AgentFn:
    rng = random.Random(seed)

    def random_agent(_observation: dict[str, Any] | None, _tick: int) -> Action:
        return Action(
            forward=rng.uniform(-1.0, 1.0),
            strafe=rng.uniform(-1.0, 1.0),
            yaw_delta=rng.uniform(-15.0, 15.0),
            pitch_delta=rng.uniform(-5.0, 5.0),
            jump=rng.random() < 0.1,
            attack=rng.random() < 0.4,
            sprint=rng.random() < 0.3,
            hotbar_slot=rng.randint(0, 8),
        )

    return random_agent
