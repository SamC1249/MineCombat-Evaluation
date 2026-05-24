We use paper, gradlew, Temurin JDK 21, tested on MacOS.
Commands: `./scripts/run-gradle.sh build`. Need JDK 21 (Gradle) and 25 (Paper). Default eval world name: **`mcbench_flat`** (superflat); see `server/server.properties.example`.

Python MVP0: stdlib client in `minecombat_eval/`; run `python3 run_eval.py` from repo root (player must be online). Logs append to `episodes.jsonl` by default.

**L1 task_spec grid:** `benchmarks/l1-v1/` (36 tasks); `python3 benchmarks/generate_l1_grid.py`; `python3 run_suite.py --suite benchmarks/l1-v1/suite.json`.

**L2 custom envs:** `CaveRoom-*` + `BeachRoom-*` (17 scenarios each); suites `benchmarks/l2-*-v1/`; mob griefing off (`disable-mob-griefing`). **MVP 1.0** = L1/L2 scenarios + suites + `run_eval.py` / `run_suite.py`; eval logs gitignored (`episodes.jsonl`, `results/`).

MVP1 plan: `planning/mvp1.md`; checklist in `planning/tasks.md`.
