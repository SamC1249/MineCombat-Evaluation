# Observation schema v1

Tied to **protocol v1** (`planning/protocol-v1.md`). Observations appear on `reset_ok` and every `step_result`.

Agents should treat unknown top-level or nested fields as optional and ignore them.

---

## Top-level shape

```json
{
  "tick": 17,
  "player": { },
  "mobs": [ ],
  "meta": { }
}
```

| Key | Required | Type | Notes |
|-----|----------|------|-------|
| `tick` | yes | int | Server tick since episode reset (0 on reset) |
| `player` | yes | object | Evaluated player state |
| `mobs` | yes | array | Hostile entities in arena range (may be empty) |
| `meta` | yes | object | Scenario and run metadata |

**Not in observation:** actions (`forward`, `attack`, etc.) are client → server only. No pixels, inventory, or block grid in v1.

---

## `player` object

| Field | Type | Range / notes |
|-------|------|----------------|
| `health` | float | Current HP |
| `max_health` | float | Attribute max (usually 20) |
| `food` | int | Hunger level 0–20 |
| `x`, `y`, `z` | float | Position |
| `yaw`, `pitch` | float | Look angles (degrees) |
| `on_ground` | bool | Feet on ground |

---

## `mobs[]` entries

Each element describes one **arena hostile** tracked for the episode:

| Field | Type | Notes |
|-------|------|-------|
| `kind` | string | Bukkit entity type, e.g. `ZOMBIE`, `CREEPER` |
| `uuid` | string | Entity UUID |
| `x`, `y`, `z` | float | Position |
| `health` | float | Current HP |
| `distance` | float | Euclidean distance to player |

Order is not guaranteed. For targeting, pick e.g. minimum `distance`.

---

## `meta` object — stability contract

These keys are **guaranteed for benchmark comparability** when using registered scenarios:

| Key | Type | Always present |
|-----|------|----------------|
| `plugin_version` | string | yes |
| `paper_minecraft` | string | yes (runtime string from server) |
| `scenario_id` | string | yes |
| `scenario_version` | string | yes |
| `scenario_level` | int | yes (1 = template arena, 2 = custom env) |
| `time_of_day` | string | yes (`day`, `night`, `custom`, …) |
| `world_time` | int | yes (0–24000 overworld tick set on reset) |
| `hostile_entity` | string | yes (primary entity type for scenario) |
| `hostile_count` | int | yes (tracked hostiles this episode) |

**Level 2 extensions** (present when scenario uses a custom environment):

| Key | Type | When |
|-----|------|------|
| `environment_id` | string | L2 only, e.g. `cave`, `beach` |
| `task_spec_applied` | bool | When reset merged TCP/`task_spec` overrides |
| `baby_zombie` | bool | Baby zombie scenarios only |

Do not rely on other `meta` keys for benchmark logic unless documented in a future protocol version.

---

## Examples

### Minimal (no hostiles visible yet)

```json
{
  "tick": 0,
  "player": {
    "health": 20.0,
    "max_health": 20.0,
    "food": 20,
    "x": -39.0,
    "y": -60.0,
    "z": 12.0,
    "yaw": 0.0,
    "pitch": 0.0,
    "on_ground": true
  },
  "mobs": [],
  "meta": {
    "plugin_version": "0.1.0-SNAPSHOT",
    "paper_minecraft": "26.1.x",
    "scenario_id": "ZombieRoom-v0",
    "scenario_version": "1",
    "scenario_level": 1,
    "time_of_day": "day",
    "world_time": 1000,
    "hostile_entity": "ZOMBIE",
    "hostile_count": 1
  }
}
```

### Multi-mob (L2 or task_spec)

```json
{
  "tick": 42,
  "player": { "health": 16.0, "max_health": 20.0, "food": 20, "x": -50.0, "y": -58.0, "z": 34.0, "yaw": 45.0, "pitch": -5.0, "on_ground": true },
  "mobs": [
    { "kind": "ZOMBIE", "uuid": "…", "x": -44.0, "y": -58.0, "z": 30.0, "health": 12.0, "distance": 6.2 },
    { "kind": "SKELETON", "uuid": "…", "x": -46.0, "y": -58.0, "z": 31.0, "health": 18.0, "distance": 4.1 }
  ],
  "meta": {
    "scenario_id": "CaveRoom-v0",
    "scenario_level": 2,
    "environment_id": "cave",
    "hostile_count": 2,
    "task_spec_applied": true
  }
}
```

---

## Implementing an agent

1. Parse `player` and `mobs` each tick.
2. Read `meta.scenario_id` / `scenario_level` for logging only (do not branch on undocumented keys).
3. Return an `Action` (see protocol v1) with movement relative to player facing.
4. Terminal signal comes from `step_result` (`terminated`, `outcome`, `reason`), not from observation.

Reference baseline: `minecombat_eval.reference_policy.ReferenceCombatPolicy`.

---

## Related

- Wire messages: `planning/protocol-v1.md`
- Agent integration: `planning/agent-integration.md`
- Environment blurbs: `planning/benchmark-cards.md`
