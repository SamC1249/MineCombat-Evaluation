# MineCombat-Evaluation

Paper plugin + TCP JSON protocol for combat-survival eval. Protocol: `planning/protocol-v1.md`.

## Building the plugin

Use **JDK 21** for Gradle (not Java 25+ for the Gradle daemon):

```bash
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

- `JAVA_HOME` → Temurin **21** for `./gradlew`
- `SERVER` → your Paper directory
- `USER_UUID` → your Minecraft profile UUID (for **your** tooling only; plugin uses **username** in `config.yml` if set)

`.env` is listed in `.gitignore`; do not commit secrets you care about.
