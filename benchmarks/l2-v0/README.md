# Level 2 custom environments

Two built-in arenas with unique spawn locations (see `evaluation.environments` in plugin `config.yml`):

| Environment | Player spawn | Hostile anchor | Scenario prefix |
|-------------|--------------|----------------|-----------------|
| **cave** | -50, -58, 34 | -44, -58, 30 | `CaveRoom-*` |
| **beach** | -16, 61, 27 | -12, 61, 32 | `BeachRoom-*` |

Each environment has **17 scenarios** (13 mob types + 4 gear/time variants), mirroring Level 1.

## Run suites

```bash
python3 run_suite.py --suite benchmarks/l2-cave-v1/suite.json -o results/l2-cave.jsonl
python3 run_suite.py --suite benchmarks/l2-beach-v1/suite.json -o results/l2-beach.jsonl
```

Single scenario:

```bash
python3 run_eval.py --scenario CaveRoom-v0-creeper --episodes 1
python3 run_eval.py --scenario BeachRoom-v0-skeleton --episodes 1
```

## Multiple mobs

Via `task_spec` on reset (or `--task-json`):

```json
{
  "entities": [
    { "entity": "ZOMBIE", "count": 2 },
    { "entity": "SKELETON", "x": -44, "y": -58, "z": 30 }
  ]
}
```

See `examples/task_spec_multi_mob.json`.

Or in scenario YAML:

```yaml
hostiles:
  - entity: ZOMBIE
    count: 2
  - entity: CREEPER
    count: 1
```

## Regenerate

```bash
python3 benchmarks/generate_l2_config.py   # config.yml scenarios
python3 benchmarks/generate_l2_suites.py   # suite.json manifests
```

Restart Paper after config/JAR changes.
