# L1-v1 benchmark grid

**36 tasks** = 6 mobs × 3 gear tiers × day/night, all on the Level 1 template arena.

| Dimension | Values |
|-----------|--------|
| Mobs | zombie, creeper, skeleton, spider, enderman, witch |
| Gear | `wood`, `stone`, `iron_full` |
| Time | `day`, `night` |

Each task is a `task_spec` JSON merged onto base scenario `ZombieRoom-v0`.

## Regenerate

```bash
python3 benchmarks/generate_l1_grid.py
```

Edit `MOBS`, `GEAR_TIERS`, or `TIMES` in that script, then regenerate.

## Run full suite

Paper running, player online:

```bash
python3 run_suite.py --suite benchmarks/l1-v1/suite.json -o results/l1-v1.jsonl
```

Filter examples:

```bash
# One mob family
python3 run_suite.py --suite benchmarks/l1-v1/suite.json --tasks creeper_wood_day,creeper_wood_night

# All night tasks
python3 run_suite.py --suite benchmarks/l1-v1/suite.json --tags time_night

# Multiple seeds per task
python3 run_suite.py --suite benchmarks/l1-v1/suite.json --episodes 5 --seed-base 0
```

Task ids follow `{mob}_{gear}_{time}` (e.g. `skeleton_iron_full_night`).
