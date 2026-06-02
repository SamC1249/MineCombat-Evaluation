# Wire protocol v1 (MVP0)

Transport: **TCP**, **one JSON object per line** (UTF-8 newline `\n` delimiter). Bind defaults to **127.0.0.1** only.

All messages include `"protocol": 1` where noted. Unknown fields should be ignored by receivers.

## Outcomes (`outcome` / `reason`)

| `outcome`   | Meaning |
|------------|---------|
| `success`  | Episode success (e.g. all hostiles cleared, player alive). |
| `failure`  | Episode failed (e.g. player died). |
| `timeout`  | Hit `max_ticks` (`truncated` true). |

`reason` is a short machine-readable tag, e.g. `all_hostiles_defeated`, `player_died`, `max_ticks`.

## Client → server

### `reset`

Starts a new episode. **Requires an online player** (see server `config.yml`).

```json
{
  "type": "reset",
  "protocol": 1,
  "scenario_id": "ZombieRoom-v0",
  "seed": 42
}
```

- `scenario_id`: official scenario name; unknown IDs may error.
- `seed`: recorded for logging; world RNG uses server rules unless extended later.

### `step`

One control tick. **One step ≈ one server tick (20/s)** after reset.

```json
{
  "type": "step",
  "protocol": 1,
  "episode_id": "<uuid>",
  "action": {
    "forward": 0.0,
    "strafe": 0.0,
    "yaw_delta": 0.0,
    "pitch_delta": 0.0,
    "jump": false,
    "attack": false,
    "sprint": false,
    "hotbar_slot": 0
  }
}
```

- `forward` / `strafe`: roughly \([-1,1]\), relative to player facing.
- `yaw_delta` / `pitch_delta`: degrees added this tick.
- `attack`: melee swing; server resolves target.
- `hotbar_slot`: `0`–`8`.

## Server → client

### `reset_ok`

```json
{
  "type": "reset_ok",
  "protocol": 1,
  "episode_id": "<uuid>",
  "tick": 0,
  "observation": { },
  "truncated": false,
  "terminated": false
}
```

### `step_result`

```json
{
  "type": "step_result",
  "protocol": 1,
  "episode_id": "<uuid>",
  "tick": 17,
  "reward": 0.0,
  "truncated": false,
  "terminated": false,
  "outcome": null,
  "reason": null,
  "observation": { }
}
```

When the episode ends, **`terminated` is true** and `outcome` / `reason` are set (terminal row for logging).

### `error`

```json
{
  "type": "error",
  "protocol": 1,
  "message": "human-readable"
}
```

## `observation` (v1)

```json
{
  "tick": 17,
  "player": {
    "health": 18.5,
    "max_health": 20.0,
    "food": 20,
    "x": 0.0, "y": -60.0, "z": 0.0,
    "yaw": 90.0, "pitch": 0.0,
    "on_ground": true
  },
  "mobs": [
    {
      "kind": "ZOMBIE",
      "uuid": "<uuid>",
      "x": 3.2, "y": -60.0, "z": 1.0,
      "health": 14.0,
      "distance": 3.4
    }
  ],
  "meta": {
    "plugin_version": "0.1.0-SNAPSHOT",
    "paper_minecraft": "26.1.x (runtime)",
    "scenario_id": "ZombieRoom-v0",
    "scenario_version": "1",
    "scenario_level": 1,
    "time_of_day": "day",
    "world_time": 1000
  }
}
```

- `meta.paper_minecraft` is best-effort from the running server.
- `scenario_id` / `scenario_version` / `scenario_level` identify the active scenario. **Level 1** uses the template superflat arena; **Level 2** uses custom environments (`environment_id`: `cave`, `beach`) at fixed coordinates — see `planning/world-setup.md`.
- `time_of_day` is a short label (`day`, `night`, `custom`, …); `world_time` is the overworld time tick (0–24000) set on `reset`.
- Full field reference and stability contract: **`planning/observation-v1.md`**.
