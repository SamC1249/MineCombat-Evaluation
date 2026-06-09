# Porting a policy to MineCombat-Evaluation

This guide takes you from "I have an agent" to "it runs on the benchmark." The
fast path is three commands:

```bash
minecombat-eval init-policy my_agent --kind conditional         # 1. scaffold
minecombat-eval test-policy my_agent.policy:MyAgentPolicy        # 2. validate offline
minecombat-eval run-suite l1-v1 --policy my_agent.policy:MyAgentPolicy -o results/l1.jsonl  # 3. run
```

Step 2 needs **no Minecraft server** — it runs your policy against synthetic
observations and checks the outputs. Do all your debugging there before touching
a live server.

---

## 1. The policy contract

A policy maps an observation to an action each tick. Implement
[`minecombat_eval.Policy`](../minecombat_eval/policy.py):

```python
from minecombat_eval import Action, Policy

class MyPolicy(Policy):
    def reset(self, ctx: dict) -> None:    # optional; called once per episode
        ...                                # ctx: scenario_id, seed (+ suite_id/task_id in suites)

    def act(self, observation: dict | None, tick: int) -> Action:  # required
        return Action()
```

A plain callable `(observation, tick) -> Action` also works anywhere a policy is
accepted — handy for stateless agents or quick experiments.

Load it with the `module:attr` spec used by every command:

```bash
--policy my_agent.policy:MyPolicy
```

`module` is the import path (must be importable: installed, or on `PYTHONPATH`,
or run from its directory). A class is instantiated for you; an instance or
callable is used as-is.

---

## 2. The `Action` fields

[`Action`](../minecombat_eval/models.py) is a dataclass; all fields default to
"do nothing":

| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| `forward` | float | `-1.0`…`1.0` | Move forward/back relative to facing |
| `strafe` | float | `-1.0`…`1.0` | Move right/left relative to facing |
| `yaw_delta` | float | per-tick turn | Change in horizontal look (degrees) |
| `pitch_delta` | float | per-tick turn | Change in vertical look (degrees) |
| `jump` | bool | — | Jump this tick |
| `attack` | bool | — | Swing/attack this tick |
| `sprint` | bool | — | Sprint while moving |
| `hotbar_slot` | int | `0`…`8` | Selected hotbar slot |

Movement is **relative to where the player is facing**, so aim first, then move
forward. The reference baseline clamps `yaw_delta` to ±15° and `pitch_delta` to
±8° per tick; large jumps look unnatural and overshoot.

The observation schema (`player`, `mobs[]`, `meta`) is documented in
[`planning/observation-v1.md`](../planning/observation-v1.md).

---

## 3. Helpers — skip the boilerplate

Import from the package top level ([`minecombat_eval.helpers`](../minecombat_eval/helpers.py)):

| Helper | Returns |
|--------|---------|
| `nearest_mob(obs)` | Closest hostile dict, or `None` |
| `mobs_by_distance(obs)` | All hostiles, nearest first |
| `mob_distance(obs, mob)` | Distance (uses `distance` field or computes it) |
| `aim_at(player, target, ...)` | Clamped `(yaw_delta, pitch_delta)` toward target |
| `player_health_fraction(obs)` | HP fraction `0.0`–`1.0`, or `None` |
| `clamp` / `normalize_yaw` | Small math utilities |
| `validate_action(action)` | List of problems (`[]` = valid) |

A complete combat agent in a few lines:

```python
from minecombat_eval import Action, Policy, aim_at, nearest_mob

class MyPolicy(Policy):
    def act(self, observation, tick):
        target = nearest_mob(observation)
        if target is None:
            return Action()
        yaw, pitch = aim_at(observation["player"], target)
        dist = target["distance"]
        return Action(forward=1.0 if dist > 3 else 0.0,
                      yaw_delta=yaw, pitch_delta=pitch,
                      attack=dist <= 3.2)
```

See [`examples/custom_policy/`](../examples/custom_policy/) for scripted,
conditional, and PyTorch versions you can run today.

---

## 4. Test offline before going live

```bash
minecombat-eval test-policy my_agent.policy:MyAgentPolicy
```

This imports your policy and runs `act()` across an episode of synthetic
observations (a mob walking toward the player, so every distance regime is
exercised), then validates each `Action`. It catches, with a clear message and
exit code:

- import errors / wrong `module:attr`
- a class that doesn't subclass `Policy`, or a non-callable target
- exceptions raised in `reset()` or `act()` (with traceback + the failing tick)
- actions that aren't `Action`, contain NaN/inf, or fall outside legal ranges

Options: `--ticks N` (default 60), `--scenario ID` (sets `scenario_id` in the
fake observation). Build the same fake observations in your own unit tests via
[`minecombat_eval.synthetic`](../minecombat_eval/synthetic.py)
(`fake_observation`, `fake_mob`, `approach_episode`).

---

## 5. Wrapping a PyTorch model

PyTorch is **not** a dependency of this benchmark — `pip install torch`
yourself. The pattern (see [`torch_policy.py`](../examples/custom_policy/torch_policy.py)
or scaffold with `--kind torch`):

1. Lazy-import `torch` in `__init__` so the package stays importable without it.
2. Load the model (`torch.jit.load` for `.pt`, `torch.load` otherwise), call `.eval()`.
3. `_features(obs)` → input vector; run under `torch.no_grad()`.
4. `_to_action(output)` → `Action`, clamping each field to its legal range.

```bash
MINECOMBAT_MODEL=path/to/model.pt \
  minecombat-eval test-policy my_agent.policy:MyAgentPolicy
```

---

## 6. Packaging & import troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: my_agent` | Not importable. Run from the package's parent dir, `pip install -e .`, or set `PYTHONPATH`. |
| `init-policy: invalid name 'my-agent'` | Module names use underscores: `my_agent`, not `my-agent`. |
| `class must subclass ... Policy` | Subclass `minecombat_eval.Policy`, or pass a `(obs, tick) -> Action` callable. |
| `expected module.path:ClassOrCallable` | The spec needs a colon: `my_agent.policy:MyPolicy`. |
| `not a Policy subclass/instance or callable` | The named attribute isn't a policy class, instance, or function. |

Run `test-policy` first — most of these surface there in under a second instead
of after a server spin-up.

---

## Related

- Observation schema — [`planning/observation-v1.md`](../planning/observation-v1.md)
- Agent integration & modes — [`planning/agent-integration.md`](../planning/agent-integration.md)
- Reference baseline — [`minecombat_eval/reference_policy.py`](../minecombat_eval/reference_policy.py)
