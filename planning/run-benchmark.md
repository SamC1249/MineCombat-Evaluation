# Run the benchmark (one path)

Follow these steps in order. No Java or Python source reading required.

**Fastest path:** `pip install -e .` → `minecombat-eval bootstrap` → join server → run suite.  
**Docker:** `docker compose up --build` → join `localhost:25565` → eval on port `8765`.

---

## 0. One-command bootstrap (recommended)

```bash
cp .env.example .env   # set JAVA_21, JAVA_25, SERVER
python3 -m venv .venv && source .venv/bin/activate
pip install -e .       # from repo root; installs minecombat-eval CLI + world artifact

minecombat-eval bootstrap
minecombat-eval server start
```

Bootstrap downloads pinned **Paper 26.1.2**, builds the plugin JAR, installs world **`mcbench_flat-v1`** (SHA256-verified zip), and syncs `config.yml`.

Then join **localhost** in world **`mcbench_flat`**, and run:

```bash
minecombat-eval run-suite l1-v1 -o results/l1-v1-ref.jsonl
minecombat-eval summarize results/l1-v1-ref.jsonl
```

Equivalent shell script: `./scripts/bootstrap.sh`

---

## Docker

```bash
docker compose up --build
```

- Minecraft: `localhost:25565`
- Eval TCP: `localhost:8765`
- Join the server once with a Minecraft **26.1** client, then from the host:

```bash
pip install -e .
minecombat-eval run-suite l1-v1 --host 127.0.0.1 --port 8765 -o results/l1-v1-ref.jsonl
```

World + plugin + config are baked into the image (`minecombat_eval/data/mcbench_flat-v1.zip`).

---

## Manual path (step by step)

**Quick checklist:** build JAR → install on Paper → sync config → start server → join world → smoke test → run suites.

---

## 1. Prerequisites

| Requirement | Version / notes |
|-------------|-----------------|
| Python | 3.10+ (stdlib only) |
| JDK for Gradle | **21** (build plugin) |
| JDK for Paper | **25** (run server; MC 26.1) |
| Minecraft client | Java Edition matching server (**26.1**) |
| Paper server | Separate folder, not in repo |

Create **`.env`** in the repo root:

```bash
JAVA_21=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
JAVA_25=/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home
SERVER=$HOME/minecraft-paper-mcbench
```

Adjust paths for your OS. See `server/server.properties.example` for world settings.

---

## 2. Pin versions

| Component | Pinned value |
|-----------|--------------|
| Minecraft | **26.1** |
| Paper API / build | **26.1.2** (use matching `paper.jar`) |
| Plugin | **0.1.0-SNAPSHOT** |
| Protocol | **1** |
| Suite IDs | `l1-v1`, `l2-cave-v1`, `l2-beach-v1` (version **1** each) |

Record the exact Paper build from your server (`/version` in console) in lab notes when publishing.

---

## 3. Build the plugin

From repo root:

```bash
./scripts/run-gradle.sh jar
```

Output JAR:

```text
paper-plugin/build/libs/minecombat-evaluation-0.1.0-SNAPSHOT.jar
```

---

## 4. Server setup

1. Download/install Paper **26.1** as `$SERVER/paper.jar`.
2. Accept EULA: `$SERVER/eula.txt` → `eula=true`.
3. Set world in `$SERVER/server.properties`:

   ```properties
   level-name=mcbench_flat
   level-type=minecraft:flat
   ```

4. Copy the plugin JAR to `$SERVER/plugins/`.
5. **First start** (creates plugin config folder):

   ```bash
   ./scripts/run-paper.sh
   ```

   Stop the server after it finishes loading (`stop` in console).

See **`planning/world-setup.md`** for L1/L2 geometry — L2 requires pre-built arenas; the repo does not ship the world.

---

## 5. Sync config

Copy the repo template to the live server (backs up existing file by default):

```bash
./scripts/sync-config.sh
```

Options: `--dry-run` (print paths only), `--no-backup`.

**Restart Paper** after config or JAR changes. Config is loaded at plugin enable only.

---

## 6. Start server and join

```bash
./scripts/run-paper.sh
```

In Minecraft Java: **Multiplayer** → **`localhost`**.

Ensure you are in world **`mcbench_flat`**. Set `evaluation.player-name` in server config to your username, or leave empty to use the first online player (name sort).

---

## 7. Smoke test

With the server running and you online:

```bash
printf '%s\n' '{"type":"reset","protocol":1,"scenario_id":"ZombieRoom-v0","seed":1}' | nc 127.0.0.1 8765
```

Expect a JSON line with `"type":"reset_ok"`. Then one Python episode:

```bash
python3 run_eval.py --scenario ZombieRoom-v0 --episodes 1 --seed 0
```

---

## 8. Full benchmark (official baseline)

Use **ReferenceCombatPolicy** as the published heuristic baseline:

```bash
mkdir -p results

python3 run_suite.py --suite benchmarks/l1-v1/suite.json \
  --episodes 10 --seed-base 0 \
  --policy minecombat_eval.reference_policy:ReferenceCombatPolicy \
  -o results/l1-v1-ref.jsonl

python3 run_suite.py --suite benchmarks/l2-cave-v1/suite.json \
  --episodes 10 --seed-base 0 \
  --policy minecombat_eval.reference_policy:ReferenceCombatPolicy \
  -o results/l2-cave-v1-ref.jsonl

python3 run_suite.py --suite benchmarks/l2-beach-v1/suite.json \
  --episodes 10 --seed-base 0 \
  --policy minecombat_eval.reference_policy:ReferenceCombatPolicy \
  -o results/l2-beach-v1-ref.jsonl
```

Summarize:

```bash
python3 scripts/summarize_results.py results/l1-v1-ref.jsonl
```

Citation details: **`planning/benchmark-suites.md`**.

**Runtime:** L1 full suite = 36 tasks × 10 episodes = 360 serial episodes; expect long wall-clock time. Use `--tasks` or `--tags core` for dev runs.

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `unsupported scenario_id` | Stale server `config.yml` | `./scripts/sync-config.sh`, restart Paper |
| `no online player` / join errors | Client not connected | Join `localhost` in `mcbench_flat` |
| Player can't move with WASD during eval | TCP agent controls movement | Normal during `run_eval.py` / `run_suite.py`; stop the script to regain control |
| Mobs everywhere outside arena | Isolation/world border | Check `evaluation.isolation` in config; correct world name |
| L2 instant fail / void | Missing cave/beach builds | See `planning/world-setup.md` |
| Connection refused on 8765 | Plugin not loaded or wrong port | Check server log; `network.port` in config |
| `player disconnected` mid-run | Left the server during eval | Rejoin and restart the run |

---

## Related docs

| Doc | Purpose |
|-----|---------|
| `planning/benchmark-suites.md` | Suite IDs, seeds, paper template |
| `planning/world-setup.md` | World name, L1/L2 coordinates |
| `planning/agent-integration.md` | Custom policies |
| `planning/observation-v1.md` | Observation schema for agents |
| `planning/commands-and-scenarios.md` | All scenario IDs and CLI flags |
