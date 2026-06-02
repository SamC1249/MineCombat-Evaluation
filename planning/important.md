We use paper, gradlew, Temurin JDK 21, tested on MacOS.
Commands: `./scripts/run-gradle.sh build`. Need JDK 21 (Gradle) and 25 (Paper). Default eval world name: **`mcbench_flat`** (superflat); see `server/server.properties.example`.

Python MVP0: stdlib client in `minecombat_eval/`; run `python3 run_eval.py` from repo root (player must be online). Logs append to `episodes.jsonl` by default.

**L1 task_spec grid:** `benchmarks/l1-v1/` (36 tasks); `python3 benchmarks/generate_l1_grid.py`; `python3 run_suite.py --suite benchmarks/l1-v1/suite.json`.

**L2 custom envs:** `CaveRoom-*` + `BeachRoom-*` (17 scenarios each); suites `benchmarks/l2-*-v1/`; mob griefing off (`disable-mob-griefing`). **MVP 1.0** = L1/L2 scenarios + suites + `run_eval.py` / `run_suite.py`; eval logs gitignored.

**Research-ready (Tier 1+2):** One-page run path `planning/run-benchmark.md`; suites `planning/benchmark-suites.md`; world `planning/world-setup.md`; baseline `ReferenceCombatPolicy`; `scripts/sync-config.sh`; obs `planning/observation-v1.md`; cards `planning/benchmark-cards.md`; `scripts/summarize_results.py`.

**Distribution (Tier 3 partial):** `minecombat-eval bootstrap` / `pip install -e .`; versioned world `minecombat_eval/data/mcbench_flat-v1.zip`; `docker compose up`. Master plan: `planning/research-ready-plan.md`.

MVP1 plan: `planning/mvp1.md`; checklist in `planning/tasks.md`.
