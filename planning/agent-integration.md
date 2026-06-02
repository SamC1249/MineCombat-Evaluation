# Agent integration (benchmark-first)

## Modes

1. **Eval over TCP (default)** — Your code maps `observation` → `Action` each tick. Train offline or elsewhere; no Gym dependency.
2. **`MineCombatEnv`** — `reset` / `step` in `minecombat_eval.env` for RL-style loops; reward stays `0.0` until the server defines shaping.
3. **Offline** — Use `episodes.jsonl` (and future traces) without a live server.

## Custom policy

Implement `minecombat_eval.policy.Policy`:

- `reset(ctx)` — optional; `ctx` includes `scenario_id`, `seed`.
- `act(observation, tick)` → `Action`.

Or provide a plain **callable** `(observation, tick) -> Action` (same as `AgentFn`).

### `run_eval.py`

```bash
python3 run_eval.py --policy minecombat_eval.reference_policy:ReferenceCombatPolicy --scenario ZombieRoom-v0
python3 run_suite.py --suite benchmarks/l1-v1/suite.json \
  --policy minecombat_eval.reference_policy:ReferenceCombatPolicy -o results/l1-v1-ref.jsonl
```

`--policy module:Name` loads a **Policy subclass** (instantiated automatically) or a callable.

Stub agents: `--agent noop|random` when `--policy` is omitted.

### Official baseline: `ReferenceCombatPolicy`

Heuristic combat agent (no ML): targets nearest hostile in `observation.mobs`, aims with clamped yaw/pitch deltas, closes distance, attacks in range. Use for paper comparisons — see `planning/benchmark-suites.md`.

```bash
python3 run_eval.py --policy minecombat_eval.reference_policy:ReferenceCombatPolicy --episodes 5 --seed-base 0
```

Example noop policy: `minecombat_eval.reference_policy:NoopPolicy`.

## Level 1 scenarios

All use the **same** arena and spawns from server `config.yml`; only **gear**, **time-of-day**, and optional **max-ticks** change. See `evaluation.scenarios` in the plugin config.

**Level 2** (`CaveRoom-*`, `BeachRoom-*`) uses fixed environments in `evaluation.environments` — see `planning/world-setup.md`.

## Reward (current)

The server sends **`reward: 0.0`** on each `step_result`. Treat **terminal** `outcome` / `reason` as the benchmark signal until optional shaping is added to the protocol.

## Observation

Full schema: **`planning/observation-v1.md`**. Wire format: `planning/protocol-v1.md`. Check `observation.meta` for `scenario_id`, `scenario_version`, `scenario_level`, `time_of_day`, `world_time`, and L2 `environment_id`.
