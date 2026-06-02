# Benchmark cards

Short descriptions for papers and README. Coordinates: `planning/ground_truths/positions.md` and `planning/world-setup.md`.

---

## L1 template arena (`ZombieRoom-*`)

Single superflat combat room at y = −60. One primary hostile per episode (type varies by scenario or `task_spec`). Player receives scenario gear (wood / stone / iron sword tiers). Success when **all tracked hostiles are defeated** and the player is alive; failure on player death; timeout at `max_ticks` (default **2400** ≈ 2 minutes).

| Property | Value |
|----------|-------|
| World | `mcbench_flat` |
| Level | 1 |
| Default mobs | 1 hostile |
| Success | `outcome: success`, reason `all_hostiles_defeated` |
| Failure | `outcome: failure`, reason `player_died` |
| Timeout | `outcome: timeout`, reason `max_ticks`, `truncated: true` |
| Max ticks | 2400 (scenario/task override allowed) |

---

## L1-v1 grid (`l1-v1` suite)

Curated **36 tasks**: 6 mob families × 3 gear tiers × day/night. Base scenario **`ZombieRoom-v0`** with per-task JSON overrides (`entity`, `gear`, `time_of_day`). Skill families include baseline melee, explosion pressure (creeper), ranged kiting (skeleton), fast melee (spider), teleport melee (enderman), potion ranged (witch).

| Property | Value |
|----------|-------|
| Suite ID | `l1-v1` v1 |
| Tasks | 36 |
| Citation | MineCombat-Eval L1-v1 |
| Manifest | `benchmarks/l1-v1/suite.json` |

---

## L2 cave (`CaveRoom-*`, `l2-cave-v1`)

Underground arena at fixed coordinates (−50, −58, 34 player spawn). Low light, enclosed space; emphasizes close combat and explosion pressure (creeper). **17 scenarios** (13 mob variants + 4 gear/time). Requires **pre-built cave geometry** in `mcbench_flat`.

| Property | Value |
|----------|-------|
| Environment | `cave` |
| Level | 2 |
| Player spawn | −50, −58, 34 |
| Default max ticks | 2400 |
| Success / fail / timeout | Same terminal rules as L1 |
| Suite ID | `l2-cave-v1` v1 (17 tasks) |

---

## L2 beach (`BeachRoom-*`, `l2-beach-v1`)

Surface beach arena at (−16, 61, 27). Open sight lines; suited to ranged mobs and kiting. **17 scenarios** mirroring cave mob coverage. Requires **pre-built beach geometry** in `mcbench_flat`.

| Property | Value |
|----------|-------|
| Environment | `beach` |
| Level | 2 |
| Player spawn | −16, 61, 27 |
| Default max ticks | 2400 |
| Success / fail / timeout | Same terminal rules as L1 |
| Suite ID | `l2-beach-v1` v1 (17 tasks) |

---

## Official baseline

**ReferenceCombatPolicy** — heuristic aim/chase/attack (no ML). Use for comparable numbers in papers:

```bash
--policy minecombat_eval.reference_policy:ReferenceCombatPolicy
```

See `planning/benchmark-suites.md` for full run commands and reporting protocol.
