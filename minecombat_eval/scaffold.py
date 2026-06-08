"""Generate an importable, runnable policy package (``minecombat-eval init-policy``)."""

from __future__ import annotations

import keyword
from pathlib import Path

KINDS = ("scripted", "conditional", "torch")


class ScaffoldError(Exception):
    """User-facing error for invalid scaffold requests."""


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def validate_package_name(name: str) -> None:
    """Reject names Python can't import as a module/package."""
    if not name:
        raise ScaffoldError("policy name is required, e.g. my_agent")
    if "-" in name:
        suggestion = name.replace("-", "_")
        raise ScaffoldError(
            f"invalid name {name!r}: Python import paths use underscores, not hyphens "
            f"(try {suggestion!r})"
        )
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ScaffoldError(
            f"invalid name {name!r}: must be a valid Python identifier "
            "(letters, digits, underscores; not starting with a digit), e.g. my_agent"
        )


def _scripted_template(cls: str) -> str:
    return f'''"""Scripted policy: a fixed action sequence, ignores the observation.

Useful as a smoke test (does the eval loop run end to end?) before you add logic.
"""

from __future__ import annotations

from typing import Any

from minecombat_eval import Action, Policy


class {cls}(Policy):
    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        # Walk forward, swing every other tick. Replace with your own script.
        return Action(forward=1.0, attack=(tick % 2 == 0))
'''


def _conditional_template(cls: str) -> str:
    return f'''"""Conditional heuristic policy: react to the nearest hostile each tick.

Uses the helpers in ``minecombat_eval`` so you only write the decision logic.
"""

from __future__ import annotations

from typing import Any

from minecombat_eval import Action, Policy, aim_at, nearest_mob


class {cls}(Policy):
    def reset(self, ctx: dict[str, Any]) -> None:
        # ctx has scenario_id, seed, and (in suites) suite_id/task_id. Reset any
        # per-episode state here.
        pass

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        target = nearest_mob(observation)
        if target is None or not isinstance(observation, dict):
            return Action()

        player = observation["player"]
        dist = float(target.get("distance", 99.0))
        yaw_delta, pitch_delta = aim_at(player, target)

        return Action(
            forward=1.0 if dist > 3.0 else 0.0,
            yaw_delta=yaw_delta,
            pitch_delta=pitch_delta,
            sprint=dist > 6.0,
            attack=dist <= 3.2,
        )
'''


def _torch_template(cls: str) -> str:
    return f'''"""PyTorch policy wrapper: load a .pt model and map observation -> Action.

PyTorch is NOT a dependency of minecombat-eval; install it yourself:
    pip install torch

Set the model path via the MODEL_PATH constant or the MINECOMBAT_MODEL env var.
Edit ``_features`` and ``_to_action`` to match your model's I/O.
"""

from __future__ import annotations

import os
from typing import Any

from minecombat_eval import Action, Policy, clamp, nearest_mob

MODEL_PATH = os.environ.get("MINECOMBAT_MODEL", "model.pt")


class {cls}(Policy):
    def __init__(self, model_path: str = MODEL_PATH) -> None:
        try:
            import torch
        except ImportError as e:  # pragma: no cover - depends on user env
            raise ImportError(
                "this policy needs PyTorch: pip install torch"
            ) from e
        self._torch = torch
        self._model = torch.jit.load(model_path) if model_path.endswith(".pt") else torch.load(model_path)
        self._model.eval()

    def _features(self, observation: dict[str, Any] | None) -> list[float]:
        """Flatten the observation into your model's input vector."""
        target = nearest_mob(observation)
        if target is None or not isinstance(observation, dict):
            return [0.0, 0.0, 0.0]
        p = observation["player"]
        return [
            float(target.get("distance", 99.0)),
            float(target["x"]) - float(p["x"]),
            float(target["z"]) - float(p["z"]),
        ]

    def _to_action(self, output: Any) -> Action:
        """Map raw model output (a tensor) to a clamped Action."""
        values = [float(v) for v in output.flatten().tolist()]
        values += [0.0] * (4 - len(values))
        return Action(
            forward=clamp(values[0], -1.0, 1.0),
            strafe=clamp(values[1], -1.0, 1.0),
            yaw_delta=clamp(values[2], -15.0, 15.0),
            pitch_delta=clamp(values[3], -8.0, 8.0),
        )

    def act(self, observation: dict[str, Any] | None, tick: int) -> Action:
        torch = self._torch
        x = torch.tensor([self._features(observation)], dtype=torch.float32)
        with torch.no_grad():
            output = self._model(x)
        return self._to_action(output)
'''


_TEMPLATES = {
    "scripted": _scripted_template,
    "conditional": _conditional_template,
    "torch": _torch_template,
}


def init_policy(name: str, *, kind: str = "conditional", directory: Path | None = None) -> tuple[Path, str]:
    """Create ``<dir>/<name>/{__init__.py,policy.py}``.

    Returns ``(package_dir, policy_spec)`` where ``policy_spec`` is the
    ``module:Class`` string to pass to ``--policy``.
    """
    validate_package_name(name)
    if kind not in _TEMPLATES:
        raise ScaffoldError(f"unknown kind {kind!r}; choose one of {', '.join(KINDS)}")

    base = (directory or Path.cwd()).resolve()
    pkg_dir = base / name
    policy_file = pkg_dir / "policy.py"
    if policy_file.exists():
        raise ScaffoldError(f"{policy_file} already exists; refusing to overwrite")

    cls = f"{_camel(name)}Policy"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text(
        f'"""{name}: a custom MineCombat-Evaluation policy."""\n\n'
        f"from .policy import {cls}\n\n"
        f'__all__ = ["{cls}"]\n',
        encoding="utf-8",
    )
    policy_file.write_text(_TEMPLATES[kind](cls), encoding="utf-8")
    return pkg_dir, f"{name}.policy:{cls}"
