# MineCombat-Evaluation

Paper plugin + TCP JSON protocol for combat-survival eval. Protocol: `planning/protocol-v1.md`. **CLI flags, all scenario ids, and quick examples:** `planning/commands-and-scenarios.md`.

## Scripts (recommended)

From the repo root, with **`JAVA_21`**, **`JAVA_25`**, and **`SERVER`** set in **`.env`**:

| Script | Uses | Purpose |
|--------|------|---------|
| `./scripts/run-gradle.sh` … | **`JAVA_21`** | Gradle (`./gradlew` args forwarded) |
| `./scripts/run-paper.sh` | **`JAVA_25`** + **`SERVER`** | Start `paper.jar` in **`$SERVER`** |

Examples:

```bash
./scripts/run-gradle.sh jar
./scripts/run-paper.sh
```

**`.env`** should define **`JAVA_21`** and **`JAVA_25`** only; optional `PATH="$JAVA_21/bin:…"` so a bare `java` defaults to **21** when you `source .env`. The **`run-*.sh`** scripts set `JAVA_HOME` from **`JAVA_21`** or **`JAVA_25`** themselves—do not require `JAVA_HOME` in `.env`.

## Building the plugin

Use **JDK 21** for Gradle (not Java 25+ for the Gradle daemon):

```bash
./scripts/run-gradle.sh build
# or manually:
export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
cd paper-plugin
./gradlew build
```

JAR: `paper-plugin/build/libs/minecombat-evaluation-0.1.0-SNAPSHOT.jar`

## Paper server folder (not in this repo)

Keep the live server outside git, e.g.:

```bash
export SERVER="$HOME/minecraft-paper-mcbench"
```

### Superflat world name (recommended)

The repo assumes a **superflat** main world named **`mcbench_flat`** (see `server/server.properties.example`). In **`$SERVER/server.properties`** set at least:

```properties
level-name=mcbench_flat
level-type=minecraft:flat
```

Use a **new** world folder (rename/delete the old `world` directory if you were using the default, or pick a fresh `level-name`). The plugin’s default `evaluation.world` matches **`mcbench_flat`**; if you already have **`$SERVER/plugins/MineCombat-Evaluation/config.yml`**, set **`evaluation.world`** there to the same string (Paper does not overwrite that file on JAR upgrade).

Install the plugin by copying the JAR into:

```text
$SERVER/plugins/minecombat-evaluation-0.1.0-SNAPSHOT.jar
```

On first run, Paper creates:

```text
$SERVER/plugins/MineCombat-Evaluation/config.yml
```

That file is what the running server reads. Defaults are also shipped inside the JAR under `config.yml`; if `config.yml` already exists, **Paper will not overwrite it** when you upgrade the JAR—edit the file on disk yourself.

### Editing evaluation coordinates (detailed)

1. **Join the world** and pick the spot you want (you used **-39, 69, 12** for the eval spawn).
2. **Stop the Paper server** (type `stop` in the server console, or Ctrl+C) so you do not edit while ticks are running—safest for a clean reload.
3. Open **`$SERVER/plugins/MineCombat-Evaluation/config.yml`** in Cursor, VS Code, or TextEdit:
   - **Go to Folder** in Finder: `Cmd+Shift+G` → paste `$HOME/minecraft-paper-mcbench/plugins/MineCombat-Evaluation`
4. Set:
   - **`evaluation.spawn.player`**: `x`, `y`, `z` where the player should stand after **`reset`** (your **-39 / 69 / 12**).
   - **`evaluation.spawn.zombie`**: nearby solid block (same **y** usually), a few blocks away so the zombie does not clip into you (repo default: **-31, 69, 12**).
   - **`evaluation.arena.center-*`**: center of the **mob-clearing** box; often same as player spawn or the middle of the fight area. **`half-size`** expands the box horizontally; **`min-y-delta` / `max-y-delta`** extend the box down/up from **`center-y`** for clearing hostile mobs.
5. **`evaluation.player-name`**: leave **`""`** to use the **first online player** (name sort), **or** set your **Minecraft username** (the name above your skin—not the UUID). The plugin does **not** read `USER_UUID` from `.env`; that variable is for your own scripts or notes.
6. Save the file.
7. **Start the server again** with Java **25** (Paper 26.1 needs JVM 25+ for bytecode 69):

```bash
./scripts/run-paper.sh
# or manually:
export JAVA_HOME="$(/usr/libexec/java_home -v 25)"
cd "$HOME/minecraft-paper-mcbench"
"$JAVA_HOME/bin/java" -Xms2G -Xmx2G -jar paper.jar --nogui
```

8. Join from **Minecraft Java Edition** (same game version as the server): **Multiplayer** → **`localhost`**.
9. Smoke-test TCP (same machine as the server):

```bash
printf '%s\n' '{"type":"reset","protocol":1,"scenario_id":"ZombieRoom-v0","seed":1}' | nc 127.0.0.1 8765
```

## Copying updated defaults from this repo

After you change `paper-plugin/src/main/resources/config.yml` and rebuild, either:

- **Merge by hand** into `$SERVER/plugins/MineCombat-Evaluation/config.yml`, or  
- Back up the server file, delete it, restart once with the new JAR so **`saveDefaultConfig()`** creates a fresh file from the JAR (only if no config exists).

## `.env` in this repo

Optional local paths (not required by Paper). Example:

- `JAVA_21` / `JAVA_25` → full paths to each JDK **Home**; no `JAVA_HOME` required
- `SERVER` → your Paper directory
- `USER_UUID` → your Minecraft profile UUID (for **your** tooling only; plugin uses **username** in `config.yml` if set)

`.env` is listed in `.gitignore`; do not commit secrets you care about.

## Python batch eval (MVP0)

Prerequisites: Paper is running with the plugin loaded, and **at least one player is online** (see `evaluation.player-name` in server `config.yml`). The TCP listener defaults to **`127.0.0.1:8765`** (see plugin `config.yml`).

From the **repo root**, with **Python 3.10+** (stdlib only; no pip packages required):

```bash
python3 run_eval.py --episodes 3 --seed-base 0 -o episodes.jsonl
```

This appends **one JSON object per line** to `episodes.jsonl` (or `--output`) for each finished episode: scenario id, seed, `episode_id`, terminal `outcome` / `reason`, `ticks`, `truncated`, protocol version, and `plugin_version` / `paper_minecraft` from the last observation when present.

Useful flags: `--scenario …`, `--seed S` (same seed every episode), `--agent noop|random`, `--policy module:PolicyClass` (custom agent; overrides `--agent`), `--host` / `--port`. For `--agent random`, optional `--agent-seed` fixes the RNG.

**Level 1 scenarios** (same superflat arena; gear + day/night + optional `entity` — see `paper-plugin/src/main/resources/config.yml` → `evaluation.scenarios`):  
`ZombieRoom-v0`, `ZombieRoom-v0-creeper`, `ZombieRoom-v0-skeleton`, `ZombieRoom-v0-enderman`, `ZombieRoom-v0-spider`, `ZombieRoom-v0-baby-zombie`, `ZombieRoom-v0-witch`, `ZombieRoom-v0-magma-cube`, `ZombieRoom-v0-slime`, `ZombieRoom-v0-hoglin`, `ZombieRoom-v0-silverfish`, `ZombieRoom-v0-blaze`, `ZombieRoom-v0-shulker`, and the `ZombieRoom-L1-*` gear variants (`wood-night`, `stone-day`, `iron-leather-day`, `iron-full-day`).  
**Level 2** (custom-built environments) is not implemented in the plugin yet.

- Custom policies: `planning/agent-integration.md`
- Gym-style wrapper (optional RL): `minecombat_eval.env.MineCombatEnv`

For day-to-day runs you **do not** need manual `nc`; use `run_eval.py` instead. Keep using `nc` only for quick smoke tests of the wire format.
