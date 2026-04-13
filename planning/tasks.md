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
- [x] Plugin loads: fixed **world + arena bounds** from `config.yml` (default `world`; adjust coordinates for your flat/test area)
- [x] Reset path: clear hostile entities in arena, teleport player, apply starting gear (`EvaluationEngine`)
- [x] Spawn rules MVP0: **one zombie** for `ZombieRoom-v0`; player/zombie death + **max tick** timeout (`CombatListener`, `EvaluationEngine`)
- [x] Embedded TCP control server: one client session at a time (`EvaluationTcpServer`)
- [x] Terminal episode info returned on last `step_result` (`terminated`, `outcome`, `reason`); Python `episodes.jsonl` still TODO

### Python side

- [ ] Minimal connector: connect, `reset(seed, scenario_id)`, `step(action)`, read `terminated` / `truncated` and final info
- [ ] Stub agent (noop or random) to validate timeouts and termination
- [ ] `run_eval.py` (or equivalent): `--scenario`, `--episodes`, `--seed` / `--seed-base`; append one row per episode (e.g. `episodes.jsonl`)
- [ ] Log row includes: scenario id, seed, outcome, duration/ticks, protocol + plugin + Paper + MC versions (as available)

### Integration and exit criteria

- [ ] Document: start Paper → start plugin listener → run Python → see N log lines without manual in-game steps
- [ ] One official scenario id for MVP0 (e.g. `ZombieRoom-v0`); second scenario deferred to Phase 1 completion

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
