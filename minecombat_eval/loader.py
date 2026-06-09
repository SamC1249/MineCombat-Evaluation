"""Resolve a ``module:attr`` policy spec into a callable (shared by run_eval/CLI)."""

from __future__ import annotations

import importlib
from typing import Any, Callable

from .agents import AgentFn
from .policy import Policy


def load_policy_entry(spec: str) -> tuple[AgentFn, Callable[[dict[str, Any]], None] | None]:
    """Import ``module.path:ClassOrCallable``.

    Accepts a :class:`Policy` subclass (instantiated automatically), a
    :class:`Policy` instance, or a plain ``(observation, tick) -> Action``
    callable. Returns ``(agent_fn, before_episode_or_None)``.
    """
    mod_path, sep, name = spec.partition(":")
    if not sep or not name:
        raise ValueError("expected module.path:ClassOrCallable (note the ':')")
    mod = importlib.import_module(mod_path)
    obj = getattr(mod, name)
    if isinstance(obj, type):
        if not issubclass(obj, Policy):
            raise TypeError(f"{spec}: class must subclass minecombat_eval.policy.Policy")
        obj = obj()
    if isinstance(obj, Policy):
        policy = obj

        def agent_fn(obs: dict[str, Any] | None, tick: int) -> Any:
            return policy.act(obs, tick)

        def before(ctx: dict[str, Any]) -> None:
            policy.reset(ctx)

        return agent_fn, before
    if callable(obj):
        return obj, None
    raise TypeError(f"{spec}: not a Policy subclass/instance or callable")
