# MineCombat-Evaluation: A Reproducible Minecraft Combat Benchmark for Agent Evaluation

**Version:** v0.2.0 research-ready preview  
**Project:** MineCombat-Evaluation  
**Protocol:** TCP JSON protocol v1  
**Runtime target:** Minecraft 26.1, Paper 26.1.2, plugin 0.1.0-SNAPSHOT

---

## Abstract

MineCombat-Evaluation is a reproducible benchmark stack for evaluating embodied combat agents in Minecraft. It provides controlled combat scenarios, a versioned TCP JSON protocol, fixed benchmark suites, a portable world artifact, a Python policy interface, and a reference baseline policy. Researchers can install the toolkit, bootstrap a pinned Paper server and world, plug in an agent, and produce citable JSONL logs for standardized reporting.

The goal is not to be a general Minecraft automation framework. The goal is to make benchmark runs reproducible enough that another researcher can cite a suite id, version, seed protocol, agent commit, and raw log format without debugging local server drift.

---

## 1. Motivation

Minecraft is a useful environment for embodied agents because it combines spatial control, partial observability, long-horizon interaction, and rich game mechanics. However, reproducible evaluation remains difficult: worlds are often local and unversioned, server configuration can drift, benchmark task ids may be undocumented, and agent integrations are frequently tied to bespoke scripts.

MineCombat-Evaluation narrows the scope to combat-survival episodes. Combat gives a compact but meaningful stress test for agent control: target selection, aim correction, distance management, kiting, survival, and terminal success/failure criteria. By focusing on a controlled benchmark stack rather than open-ended gameplay, MineCombat-Evaluation provides a practical path to comparable results.

---

## 2. Contributions

MineCombat-Evaluation v0.2.0 contributes:

- A Paper plugin that controls episode reset, player gear, hostile spawning, arena isolation, and terminal outcomes.
- A TCP JSON protocol for reset, observation, action, step result, and episode end semantics.
- A Python client and CLI (`minecombat-eval`) for bootstrapping, running suites, and summarizing logs.
- Three official benchmark suites: `l1-v1`, `l2-cave-v1`, and `l2-beach-v1`.
- A versioned world artifact, `mcbench_flat-v1`, with SHA256 verification.
- A heuristic baseline, `ReferenceCombatPolicy`, for sanity-check comparisons.
- Distribution paths through PyPI, GitHub Releases, and Docker.

---

## 3. System Overview

The system separates agent logic from the Minecraft server. Agents run in Python and communicate with the Paper plugin over a local TCP socket. Each episode starts with a `reset`, receives an initial observation, then repeatedly sends actions and receives `step_result` messages until termination.

![MineCombat system architecture](../assets/system-architecture.svg)

The server side is responsible for environment control: loading the configured world, applying isolation rules, teleporting the player, equipping gear, spawning hostiles, detecting success/failure/timeout, and encoding observations. The client side is responsible for policy execution, suite iteration, seed assignment, and JSONL logging.

---

## 4. Benchmark Suites

The benchmark ships three citable suite manifests. Each suite has a stable `suite_id`, `suite_version`, and task list.

![MineCombat benchmark suite overview](../assets/benchmark-suites.svg)

| Suite ID | Version | Tasks | Environment | Purpose |
|----------|---------|------:|-------------|---------|
| `l1-v1` | `1` | 36 | Superflat template arena | Controlled grid over mobs, gear tiers, and day/night |
| `l2-cave-v1` | `1` | 17 | Built cave arena | Enclosed terrain, low light, explosion pressure |
| `l2-beach-v1` | `1` | 17 | Built beach arena | Open terrain, ranged pressure, kiting |

Recommended reporting protocol:

```text
Seeds: episode i uses seed = seed_base + i, default seed_base = 0.
Episodes per task: 10.
Agent: policy name + git commit hash.
Baseline: include ReferenceCombatPolicy.
Logs: JSONL rows with suite_id, suite_version, task_id, seed, outcome, reason, ticks.
```

---

## 5. Reproducibility Package

Reproducibility depends on distributing not only code, but also the world geometry and runtime configuration. MineCombat-Evaluation includes a versioned world artifact:

| Artifact | Value |
|----------|-------|
| World id | `mcbench_flat-v1` |
| Level name | `mcbench_flat` |
| SHA256 | `aeef834cb4e80691a5a9f7aac385f156533224cea4f045ad1be5a1e986837ad8` |
| Package path | `minecombat_eval/data/mcbench_flat-v1.zip` |

The bootstrap command installs the pinned server stack:

```bash
minecombat-eval bootstrap
minecombat-eval server start
```

Bootstrap handles Paper download, plugin build/install, config sync, and world extraction. GitHub Releases also publish the world zip, manifest, wheel, source distribution, and checksums.

---

## 6. Agent Interface

Agents implement a small policy interface:

```python
from minecombat_eval import Action, Policy

class MyPolicy(Policy):
    def act(self, observation: dict | None, tick: int) -> Action:
        return Action(forward=1.0, attack=True)
```

The observation schema is state-based:

- `player`: health, position, yaw/pitch, food, grounded state
- `mobs`: hostile type, position, health, distance
- `meta`: plugin version, Paper runtime string, scenario id/version, level, time of day, environment id

Actions are relative controls:

- movement: `forward`, `strafe`, `jump`, `sprint`
- aim: `yaw_delta`, `pitch_delta`
- combat: `attack`, `hotbar_slot`

Terminal benchmark signal comes from `step_result`: `terminated`, `truncated`, `outcome`, `reason`, and `ticks`.

---

## 7. Baseline Policy

`ReferenceCombatPolicy` is a minimal heuristic baseline, not a learned policy. It:

1. Selects the nearest hostile from `observation.mobs`.
2. Aims toward it with clamped yaw/pitch deltas.
3. Moves forward until near melee range.
4. Strafes when too close.
5. Attacks in range.

It is intended as a published reference point and smoke-test policy. Papers should compare learned or LLM-based agents against this baseline and against simple `noop` / `random` agents when relevant.

---

## 8. Distribution

MineCombat-Evaluation is distributed through:

- **GitHub:** source, docs, suite manifests, release assets
- **PyPI:** `minecombat-eval` Python package and CLI
- **GitHub Releases:** wheel, source distribution, world artifact, manifest, checksums
- **Docker:** server image path for Paper + plugin + world

Primary quick start:

```bash
pip install minecombat-eval
minecombat-eval bootstrap
minecombat-eval server start
minecombat-eval run-suite l1-v1 -o results/l1-v1-ref.jsonl
```

---

## 9. Current Validation Status

Implemented validation:

- Docker Compose config validates.
- Bootstrap has been tested against a temporary server directory for plugin install, config sync, and world extraction.
- `ReferenceCombatPolicy` imports and loads through the policy loader.
- Existing local JSONL logs summarize correctly through `scripts/summarize_results.py`.

Full published benchmark tables should be generated after running the official suites on a clean release environment.

Template table:

| Agent | Suite | Episodes/task | Success Rate | Mean Ticks | Notes |
|-------|-------|--------------:|-------------:|-----------:|-------|
| `NoopPolicy` | `l1-v1` | 10 | TBD | TBD | Control |
| `random` | `l1-v1` | 10 | TBD | TBD | Stochastic baseline |
| `ReferenceCombatPolicy` | `l1-v1` | 10 | TBD | TBD | Official heuristic |

---

## 10. Limitations

The current benchmark is intentionally scoped:

- A Minecraft Java client/player must be online during evaluation.
- Protocol v1 is state-based; it does not include pixels, inventory state, or block grids.
- Reward shaping is not implemented; terminal outcome is the benchmark signal.
- Suite execution is serial.
- Seeds are logged for episode identity; full gameplay RNG determinism remains future work.
- The world artifact is versioned and checksummed, but future releases should publish canonical full-suite baseline results.

---

## 11. Roadmap

Near-term improvements:

- Publish full `NoopPolicy`, `random`, and `ReferenceCombatPolicy` baseline tables.
- Add headless/fake-player support to remove the manual client join.
- Add reward modes while preserving terminal-outcome reporting.
- Add richer observations under protocol v2.
- Add parallel suite sharding across multiple Paper servers.
- Expand environment families and task cards.

---

## Citation Template

> We evaluate on MineCombat-Evaluation v0.2.0 using protocol v1 and benchmark suites `l1-v1`, `l2-cave-v1`, and `l2-beach-v1` (suite version 1 each). Episodes are run with seed `seed_base + i`, `seed_base = 0`, for 10 episodes per task. The environment uses Minecraft 26.1, Paper 26.1.2, plugin 0.1.0-SNAPSHOT, and world artifact `mcbench_flat-v1`. Logs are JSONL rows containing `suite_id`, `suite_version`, `task_id`, `seed`, `outcome`, `reason`, and `ticks`.

