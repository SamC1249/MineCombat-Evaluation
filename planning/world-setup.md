# World setup for MineCombat-Evaluation

Evaluations run in a single overworld named **`mcbench_flat`**. The plugin reads `evaluation.world` from server `config.yml`; that value must match `level-name` in `server.properties`.

## World name and isolation

```properties
# $SERVER/server.properties
level-name=mcbench_flat
level-type=minecraft:flat
```

Default plugin isolation (see repo `config.yml` → `evaluation.isolation`):

- Natural mob spawning disabled (plugin spawns only)
- World border centered on the active arena (128-block diameter default)
- Daylight cycle frozen during episodes
- Mob griefing disabled (creeper block damage, etc.)
- Blocks immutable (`protect-world-blocks`): player break/place, bucket use, fire/liquid spread, decay, and bed/anchor explosions are all cancelled in the eval world so the arena stays pristine across runs

## Level 1 — template arena (superflat)

All **Level 1** scenarios share one spawn box on the superflat floor at **y = −60**.

| Role | Coordinates (x, y, z) |
|------|---------------------|
| Player spawn | −39, −60, 12 |
| Hostile spawn | −31, −60, 12 |
| Arena center | −39, −60, 12 |

A blank superflat at the wrong Y (e.g. y = 69 instead of −60) will fail silently: void fall, wrong floor, or mobs in empty air. Match coordinates in `planning/ground_truths/positions.md` and repo `config.yml`.

**Minimum for L1-only dev:** Build or use a superflat region with solid ground at y = −60 near the coordinates above.

## Level 2 — fixed geometry in the same world

**Level 2** cave and beach arenas are **pre-built structures** at fixed coordinates in **`mcbench_flat`**. They are not generated from config alone.

### Cave (`environment: cave`)

| Role | Coordinates (x, y, z) |
|------|---------------------|
| Player spawn | −50, −58, 34 |
| Hostile anchor | −44, −58, 30 |
| Arena center | −47, −58, 32 |

Scenarios use the `CaveRoom-*` prefix (17 scenarios). See `benchmarks/l2-cave-v1/suite.json`.

### Beach (`environment: beach`)

| Role | Coordinates (x, y, z) |
|------|---------------------|
| Player spawn | −16, 61, 27 |
| Hostile anchor | −12, 61, 32 |
| Arena center | −14, 61, 29.5 |

Scenarios use the `BeachRoom-*` prefix (17 scenarios). See `benchmarks/l2-beach-v1/suite.json`.

**L2 will not work** on a fresh superflat with no cave/beach builds at these coordinates. You will get void spawns, wrong terrain, or immediate failure/timeouts.

## Getting the world (versioned artifact)

The canonical world ships in-repo and in the **`minecombat-eval`** pip package:

| Field | Value |
|-------|-------|
| Artifact ID | `mcbench_flat-v1` |
| Zip | `minecombat_eval/data/mcbench_flat-v1.zip` (~5.5 MB) |
| SHA256 | `aeef834cb4e80691a5a9f7aac385f156533224cea4f045ad1be5a1e986837ad8` |

Install with one command:

```bash
minecombat-eval bootstrap
# or: ./scripts/bootstrap.sh
```

See **`artifacts/README.md`**. Maintainers re-export from the lab server: `./scripts/export-world.sh`.

### Manual fallback (if bootstrap is unavailable)

| Option | Who | Steps |
|--------|-----|--------|
| **A — Lab copy** | Researchers with access | Copy lab `mcbench_flat` into `$SERVER` |
| **B — Dev minimal** | L1 only | Superflat with solid floor at y = −60 |
| **C — Manual L2** | Advanced | Build cave/beach at listed coordinates |

## Verify before running suites

1. Join **`mcbench_flat`** in the Minecraft client.
2. Teleport to L1 coords (−39, −60, 12) — solid ground underfoot.
3. For L2: visit cave and beach coords; confirm enclosed arenas exist.
4. Run smoke test: `printf '%s\n' '{"type":"reset","protocol":1,"scenario_id":"ZombieRoom-v0","seed":1}' | nc 127.0.0.1 8765`

## Related docs

- Coordinates ground truth: `planning/ground_truths/positions.md`
- L2 scenario list: `benchmarks/l2-v0/README.md`
- Full run path: `planning/run-benchmark.md`
