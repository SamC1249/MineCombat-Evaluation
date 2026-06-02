# Official benchmark suites (cite in papers)

Three suite manifests ship in-repo. Use **`suite_id` + `suite_version` + seed protocol** when reporting results.

## Canonical suites

| Suite ID | Version | Tasks | Base scenario | Citation example |
|----------|---------|-------|---------------|------------------|
| `l1-v1` | `1` | 36 | `ZombieRoom-v0` + `task_spec` | MineCombat-Eval L1-v1 |
| `l2-cave-v1` | `1` | 17 | `CaveRoom-v0*` | MineCombat-Eval L2-cave-v1 |
| `l2-beach-v1` | `1` | 17 | `BeachRoom-v0*` | MineCombat-Eval L2-beach-v1 |

Manifest paths:

- `benchmarks/l1-v1/suite.json`
- `benchmarks/l2-cave-v1/suite.json`
- `benchmarks/l2-beach-v1/suite.json`

Each manifest’s `suite_id` and `suite_version` match this table.

## Seed and episode protocol

```text
Seeds: episode i uses seed = seed_base + i (default seed_base = 0).
Episodes per task: 10 (report mean ± std or CI offline).
Agent: policy name + git commit hash; include ReferenceCombatPolicy as baseline.
Logs: results/<suite>-ref.jsonl; fields include suite_id, task_id, outcome, ticks, seed.
```

**Note:** Seeds are logged for episode identity and reproducibility of the eval protocol. Gameplay RNG may not yet be fully seed-controlled on the server; cite seeds anyway for run identity.

## Official commands

From repo root, with Paper running and a player online:

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

Dev subset (faster):

```bash
python3 run_suite.py --suite benchmarks/l1-v1/suite.json \
  --tasks zombie_wood_day --episodes 3 --tags core \
  --policy minecombat_eval.reference_policy:ReferenceCombatPolicy
```

## JSONL row fields

Each line is one finished episode. Key fields for aggregation:

| Field | Description |
|-------|-------------|
| `suite_id` | e.g. `l1-v1` |
| `suite_version` | e.g. `1` (added by `run_suite.py`) |
| `task_id` | Suite task name |
| `scenario_id` | Plugin scenario id |
| `seed` | Episode seed |
| `outcome` | `success`, `failure`, or `timeout` |
| `reason` | e.g. `all_hostiles_defeated`, `player_died`, `max_ticks` |
| `ticks` | Episode length in server ticks |

## Post-run summary

```bash
python3 scripts/summarize_results.py results/l1-v1-ref.jsonl
python3 scripts/summarize_results.py results/*.jsonl --csv results/combined.csv
```

## Paper template paragraph

Copy and fill placeholders:

> We evaluate on **MineCombat-Eval** benchmark suites **L1-v1**, **L2-cave-v1**, and **L2-beach-v1** (suite version 1 each), using **10 episodes per task** with seeds `seed_base + i` for `i ∈ {0,…,9}` and `seed_base = 0`. Episodes run on Minecraft **26.1** with Paper **26.1.2** and plugin **0.1.0-SNAPSHOT** (protocol v1). We report success rate and mean episode length (ticks) per task, and compare against the official heuristic baseline **ReferenceCombatPolicy**. Raw logs are JSONL with fields `suite_id`, `task_id`, `seed`, `outcome`, and `ticks`.

## Related

- Run path: `planning/run-benchmark.md`
- Environment details: `planning/benchmark-cards.md`
- World requirements: `planning/world-setup.md`
