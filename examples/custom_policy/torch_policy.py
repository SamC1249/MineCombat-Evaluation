"""PyTorch policy wrapper: load a trained .pt model and map observation -> Action.

PyTorch is NOT a dependency of minecombat-eval. Install it yourself:

    pip install torch

Then point the policy at your model and validate it offline:

    MINECOMBAT_MODEL=path/to/model.pt \
      minecombat-eval test-policy examples.custom_policy.torch_policy:TorchPolicy

Edit ``_features`` (observation -> input vector) and ``_to_action`` (model
output -> Action) to match your network. The wrapper handles lazy import,
eval mode, no_grad inference, and clamping outputs to legal ranges.
"""

from __future__ import annotations

import os
from typing import Any

from minecombat_eval import Action, Policy, clamp, nearest_mob

MODEL_PATH = os.environ.get("MINECOMBAT_MODEL", "model.pt")


class TorchPolicy(Policy):
    def __init__(self, model_path: str = MODEL_PATH) -> None:
        try:
            import torch
        except ImportError as e:  # pragma: no cover - depends on user env
            raise ImportError("this policy needs PyTorch: pip install torch") from e
        self._torch = torch
        if model_path.endswith(".pt"):
            self._model = torch.jit.load(model_path)
        else:
            self._model = torch.load(model_path)
        self._model.eval()

    def _features(self, observation: dict[str, Any] | None) -> list[float]:
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
