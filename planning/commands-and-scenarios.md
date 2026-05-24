# Commands and testable environments

## In-game slash commands

The plugin does **not** register Minecraft commands (no `/mceval`, etc.). Control is **TCP JSON** on the host/port in `config.yml` (default `127.0.0.1:8765`), or via `run_eval.py`.

## Shell scripts (repo root)

| Command | Purpose |
|--------|---------|
| `./scripts/run-gradle.sh …` | Run Gradle (e.g. `jar`, `build`); uses `JAVA_21` from `.env`. |
| `./scripts/run-paper.sh` | Start Paper in `$SERVER` with `JAVA_25`. |

## Python: `run_eval.py`

From the **MineCombat-Evaluation** repo root, with Paper running and a player online:

```bash
python3 run_eval.py --help
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--scenario` | `ZombieRoom-v0` | Registered `scenario_id` (see table below). |
| `--episodes` | `1` | How many full episodes in one run. |
| `--seed-base` | `0` | Episode *i* uses `seed = seed_base + i`. |
| `--seed` | *(unset)* | If set, that seed for **every** episode. |
| `--host` | `127.0.0.1` | TCP host. |
| `--port` | `8765` | TCP port. |
| `-o` / `--output` | `episodes.jsonl` | Append one JSON line per finished episode. |
| `--agent` | `noop` | `noop` or `random` (ignored if `--policy` is set). |
| `--agent-seed` | *(unset)* | RNG for `--agent random` only. |
| `--policy` | *(unset)* | `module:Class` for a custom `Policy` or callable agent. |

**Examples**

```bash
python3 run_eval.py --episodes 2 --scenario ZombieRoom-v0-creeper -o episodes.jsonl
python3 run_eval.py --scenario ZombieRoom-L1-wood-night --agent random --agent-seed 42
```

## Quick TCP smoke test (raw JSON)

```bash
printf '%s\n' '{"type":"reset","protocol":1,"scenario_id":"ZombieRoom-v0","seed":1}' | nc 127.0.0.1 8765
```

Full wire contract: `planning/protocol-v1.md`. Message types: `reset`, `step`; responses: `reset_ok`, `step_result`, `error`.

## Scenarios (environments) in shipped `config.yml`

All use the **same** `evaluation.spawn` / `evaluation.arena` in `config.yml` unless you edit the server’s copy. The **`entity`** field sets the single hostile; omit → defaults to `ZOMBIE` (L1 night gear rows omit it → zombie).

| `scenario_id` | Hostile `entity` | Time | Notes (gear in YAML) |
|---------------|------------------|------|------------------------|
| `ZombieRoom-v0` | ZOMBIE | day | Wood sword |
| `ZombieRoom-v0-creeper` | CREEPER | day | Wood |
| `ZombieRoom-v0-skeleton` | SKELETON | day | Wood |
| `ZombieRoom-v0-enderman` | ENDERMAN | day | Wood |
| `ZombieRoom-v0-spider` | SPIDER | day | Wood |
| `ZombieRoom-v0-baby-zombie` | ZOMBIE + `baby: true` | day | Wood |
| `ZombieRoom-v0-witch` | WITCH | day | Wood |
| `ZombieRoom-v0-magma-cube` | MAGMA_CUBE | day | Wood |
| `ZombieRoom-v0-slime` | SLIME | day | Wood |
| `ZombieRoom-v0-hoglin` | HOGLIN | day | Wood |
| `ZombieRoom-v0-silverfish` | SILVERFISH | day | Wood |
| `ZombieRoom-v0-blaze` | BLAZE | day | Wood |
| `ZombieRoom-v0-shulker` | SHULKER | day | Wood |
| `ZombieRoom-L1-wood-night` | ZOMBIE | night | Wood |
| `ZombieRoom-L1-stone-day` | ZOMBIE | day | Stone sword |
| `ZombieRoom-L1-iron-leather-day` | ZOMBIE | day | Iron + leather set |
| `ZombieRoom-L1-iron-full-day` | ZOMBIE | day | Full iron + iron sword |

**Source of truth:** `paper-plugin/src/main/resources/config.yml` → `evaluation.scenarios` (and your live server file under `plugins/MineCombat-Evaluation/config.yml`).

**Level 2** (custom map) is not implemented; scenarios must have `level: 1`.

## Related

- `planning/protocol-v1.md` — JSON request/response shapes.  
- `planning/agent-integration.md` — custom policies.  
- `minecombat_eval.env` — optional Gym-style wrapper.  
