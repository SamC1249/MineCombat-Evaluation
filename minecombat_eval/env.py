"""Gym-style env wrapper over TCP (optional RL adapter; stdlib-only)."""

from __future__ import annotations

from typing import Any

from .connector import EvaluationConnector, EvaluationProtocolError
from .models import Action, PROTOCOL_VERSION


class MineCombatEnv:
    """
    Single-episode stepping over the wire. Call reset() then step() until terminated.

    Reward is 0.0 until the server defines shaping; terminal outcome is in info when done.
    """

    def __init__(
        self,
        scenario_id: str = "ZombieRoom-v0",
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        timeout: float = 130.0,
    ) -> None:
        self.scenario_id = scenario_id
        self._conn = EvaluationConnector(host=host, port=port, timeout=timeout)
        self._episode_id: str | None = None
        self._observation: dict[str, Any] | None = None
        self._tick = 0

    @property
    def observation(self) -> dict[str, Any] | None:
        return self._observation

    def reset(self, *, seed: int = 0) -> tuple[dict[str, Any], dict[str, Any]]:
        self._conn.connect()
        r = self._conn.reset(self.scenario_id, int(seed))
        if r.get("type") != "reset_ok":
            raise EvaluationProtocolError(
                f"expected reset_ok, got {r.get('type')!r}",
                raw=r,
            )
        self._episode_id = str(r["episode_id"])
        obs = r.get("observation")
        if not isinstance(obs, dict):
            raise EvaluationProtocolError("reset_ok missing observation dict", raw=r)
        self._observation = obs
        self._tick = int(r.get("tick", 0))
        info = {
            "episode_id": self._episode_id,
            "protocol": PROTOCOL_VERSION,
            "scenario_id": self.scenario_id,
        }
        return obs, info

    def step(self, action: Action) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        if self._episode_id is None:
            raise RuntimeError("call reset() first")
        sr = self._conn.step(self._episode_id, action)
        if sr.get("type") != "step_result":
            raise EvaluationProtocolError(
                f"expected step_result, got {sr.get('type')!r}",
                raw=sr,
            )
        obs = sr.get("observation")
        if not isinstance(obs, dict):
            raise EvaluationProtocolError("step_result missing observation dict", raw=sr)
        self._observation = obs
        self._tick = int(sr.get("tick", self._tick))
        terminated = bool(sr.get("terminated", False))
        truncated = bool(sr.get("truncated", False))
        reward = float(sr.get("reward", 0.0))
        info: dict[str, Any] = {
            "episode_id": self._episode_id,
            "tick": self._tick,
            "protocol": PROTOCOL_VERSION,
        }
        if terminated:
            info["outcome"] = sr.get("outcome")
            info["reason"] = sr.get("reason")
        return obs, reward, terminated, truncated, info

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> MineCombatEnv:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
