# Tasks

## MVP0 checklist

MVP0 = one scenario, one arena, Paper plugin + Python client, JSON protocol, episode logging, batch over seeds. See `planning/initial.md` Phase 1 for full product context.

### Protocol and contracts

- [x] Define message schema (versioned): `reset`, `observation`, `action`, `step_result`, `episode_end` / terminal summary → see `planning/protocol-v1.md`
- [x] Document success/fail/timeout enums and which fields are required on the wire (`planning/protocol-v1.md`)
- [x] Transport: **TCP**, **127.0.0.1** by default, newline-delimited JSON (`planning/protocol-v1.md`, `paper-plugin/src/main/resources/config.yml`)

### Java / Paper backend

- [x] Pin Minecraft + Paper versions; record in build metadata and in run logs (`paper-plugin/gradle.properties`, `plugin.yml` `api-version`)
- [x] Gradle (Groovy) project with Paper API; reproducible `build` → plugin JAR (`paper-plugin/`, `./gradlew jar`)
- [x] Plugin loads: fixed **world + arena bounds** from `config.yml` (default `mcbench_flat`; adjust coordinates for your flat/test area)
- [x] Reset path: clear hostile entities in arena, teleport player, apply starting gear (`EvaluationEngine`)
- [x] Spawn rules MVP0: **one zombie** for `ZombieRoom-v0`; player/zombie death + **max tick** timeout (`CombatListener`, `EvaluationEngine`)
- [x] Embedded TCP control server: one client session at a time (`EvaluationTcpServer`)
- [x] Terminal episode info returned on last `step_result` (`terminated`, `outcome`, `reason`); Python logs to `episodes.jsonl` via `run_eval.py`

### Python side

- [x] Minimal connector: connect, `reset(seed, scenario_id)`, `step(action)`, read `terminated` / `truncated` and final info (`minecombat_eval/connector.py`)
- [x] Stub agent (noop or random) to validate timeouts and termination (`minecombat_eval/agents.py`)
- [x] `run_eval.py`: `--scenario`, `--episodes`, `--seed` / `--seed-base`; append one row per episode (`episodes.jsonl` by default)
- [x] Log row includes: scenario id, seed, outcome, ticks, protocol + plugin + Paper + MC versions (as available)

### Integration and exit criteria

- [x] Document: start Paper → plugin TCP listener → run Python → N lines in JSONL (`README.md` “Python batch eval”)
- [x] One official scenario id for MVP0 (`ZombieRoom-v0`); second scenario deferred to Phase 1 completion

---

## MVP1 checklist

Scope and rationale: **`planning/mvp1.md`**. Builds on MVP0: **benchmark-first** (protocol + scenarios + logs); **Policy + eval path** before optional Gym/RL; multi-scenario registry; docs.

### Design and protocol

- [x] **`scenario_version`** / scenario identity in observation `meta` (`planning/protocol-v1.md`); optional **`reward`** shaping deferred
- [x] Document **three modes**: eval/TCP (default), `MineCombatEnv`, offline — `planning/agent-integration.md`
- [x] **Reward**: document sparse terminal + `reward: 0.0` until protocol shaping (`planning/agent-integration.md`)
- [x] README + `mvp1.md`: benchmark-first positioning

### Java / Paper — scenarios

- [x] **Scenario registry** (`ScenarioRegistry`, `ScenarioSpec`) — Level 1 only; Level 2 returns error until custom environments exist
- [x] **Multiple Level 1 `scenario_id`s** — gear + `time-of-day` + optional `max-ticks`; defaults in `paper-plugin/src/main/resources/config.yml`
- [x] **`meta`**: `scenario_id`, `scenario_version`, `scenario_level`, `time_of_day`, `world_time`

### Python — policies and env

- [x] **`Policy` ABC** + **`AgentFn`**; **`run_eval.py`** `--policy module:attr` (Policy subclass or callable)
- [x] **`reference_policy.NoopPolicy`** + **`planning/agent-integration.md`**
- [x] **`MineCombatEnv`** (`minecombat_eval/env.py`) — stdlib RL adapter; `reward` from wire
- [x] No **`gymnasium`** dependency; optional install left to users

### Integration and exit criteria

- [x] README: scenarios list + pointers to `mvp1.md`, `agent-integration.md`, `MineCombatEnv`
- [x] Several Level 1 scenarios + **`episodes.jsonl`** rows include `scenario_version` / `scenario_level` when present
- [x] Serial eval default; parallel = out of scope (see `mvp1.md`)

### Benchmark suite (L1 task_spec grid)

- [x] **`benchmarks/l1-v1/`** — 36 curated tasks (mob × gear × time); `benchmarks/generate_l1_grid.py` to regenerate
- [x] **`run_suite.py`** — run suite manifest, filter by `--tasks` / `--tags`, JSONL + terminal summary
- [x] JSONL rows include **`suite_id`**, **`task_id`**, **`skill_family`** when run via suite
- [x] **Level 2** cave + beach environments (custom spawns, 17 scenarios each, multi-mob via `hostiles` / `task_spec.entities`)
- [ ] Config reload without Paper restart (settings load at enable only)

---

## Backbone setup (reference)

Use this to align repo layout and local dev before building scenario logic.

| Layer | Role |
|--------|------|
| **Paper server** | Runnable Minecraft Java server with plugin API; use a **pinned** Paper build for the target MC version |
| **Plugin JAR** | Your benchmark backend: arena reset, spawning, events, JSON I/O |
| **Python package** | Client + `run_eval.py`; no Minecraft binary inside the wheel (ship or download server separately) |

**Typical dev stack**

- **JDK**: **Run Gradle with JDK 17–24** (repo tested with **Temurin 21**). The plugin **compiles** with a **Java 25** toolchain (Foojay can download it). Do **not** run Gradle on JDK 26 until Gradle supports it.
- **Build**: **Gradle** (Groovy, `build.gradle`) + **`compileOnly` `paper-api`** in `paper-plugin` (add **paperweight-userdev** later only if you need NMS / dev bundle internals)
- **Server files**: `paper.jar` (or launcher script), `eula.txt`, `server.properties`, `plugins/` containing your plugin JAR
- **World/arena**: Ship a **void/superflat** or small preset world in-repo, or generate once and commit **only** the region you need; document `level-name` / dimension used for evaluation

**Python**

- **3.10+** (or project standard); `httpx`/`websockets` or stdlib `socket` + `json` for the connector; no Minecraft Python packages required for MVP0 unless you later integrate Mineflayer/Malmo

**What not to bundle in MVP0**

- Fabric client mod, Bukkit-only APIs without Paper testing, or unpinned “latest” server — keep versions explicit for reproducibility
