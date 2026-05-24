#!/usr/bin/env python3
"""
Run a benchmark suite (task_spec grid) sequentially and log JSONL rows.

Example:
  python3 run_suite.py --suite benchmarks/l1-v1/suite.json -o results/l1-v1.jsonl
  python3 run_suite.py --suite benchmarks/l1-v1/suite.json --tags core --episodes 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from minecombat_eval.connector import EvaluationConnector, EvaluationProtocolError
from minecombat_eval.suite import BenchmarkSuite, filter_tasks, load_suite, summarize_episode_rows
from run_eval import _eprint_eval_failure, load_policy_entry, run_one_episode
from minecombat_eval.agents import AgentFn, make_random_agent, noop_agent


def _resolve_agent(args: argparse.Namespace) -> tuple[AgentFn, Any]:
    if args.policy:
        return load_policy_entry(args.policy)
    if args.agent == "random":
        return make_random_agent(seed=args.agent_seed), None
    return noop_agent, None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a MineCombat benchmark suite over TCP.")
    p.add_argument(
        "--suite",
        type=Path,
        required=True,
        help="Path to suite.json (e.g. benchmarks/l1-v1/suite.json)",
    )
    p.add_argument(
        "--tasks",
        default="",
        help="Comma-separated task_id filter (default: all tasks in suite)",
    )
    p.add_argument(
        "--tags",
        default="",
        help="Comma-separated tag filter; task must have at least one tag",
    )
    p.add_argument(
        "--episodes",
        type=int,
        default=None,
        metavar="N",
        help="Override suite episodes_per_task",
    )
    p.add_argument(
        "--seed-base",
        type=int,
        default=None,
        metavar="K",
        help="Override suite seed_base",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("-o", "--output", type=Path, default=Path("episodes.jsonl"))
    p.add_argument("--agent", choices=("noop", "random"), default="noop")
    p.add_argument("--agent-seed", type=int, default=None)
    p.add_argument("--policy", default=None, metavar="module:attr")
    p.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip printing aggregate metrics at end",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        suite = load_suite(args.suite)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"--suite: {e}", file=sys.stderr)
        return 2

    task_ids = {t.strip() for t in args.tasks.split(",") if t.strip()} or None
    tag_set = {t.strip() for t in args.tags.split(",") if t.strip()} or None
    tasks = filter_tasks(suite, task_ids=task_ids, tags=tag_set)
    if not tasks:
        print("No tasks matched filters.", file=sys.stderr)
        return 2

    episodes_per_task = args.episodes if args.episodes is not None else suite.episodes_per_task
    seed_base = args.seed_base if args.seed_base is not None else suite.seed_base
    if episodes_per_task < 1:
        print("episodes must be >= 1", file=sys.stderr)
        return 2

    try:
        agent_fn, before_ep = _resolve_agent(args)
    except (ImportError, ValueError, TypeError) as e:
        print(f"--policy: {e}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    run_idx = 0
    total_runs = len(tasks) * episodes_per_task

    with EvaluationConnector(host=args.host, port=args.port) as conn, args.output.open(
        "a", encoding="utf-8"
    ) as fh:
        for task in tasks:
            scenario_id = task.scenario_id or suite.default_scenario_id
            for ep in range(episodes_per_task):
                run_idx += 1
                seed = seed_base + ep
                try:
                    result = run_one_episode(
                        conn,
                        scenario_id,
                        seed,
                        agent_fn,
                        task_spec=task.task_spec,
                        suite_id=suite.suite_id,
                        task_id=task.task_id,
                        skill_family=task.skill_family,
                        before_episode=before_ep,
                    )
                except (EvaluationProtocolError, OSError, ConnectionError) as e:
                    _eprint_eval_failure(e)
                    print(
                        f"run {run_idx}/{total_runs} task={task.task_id} failed: {e}",
                        file=sys.stderr,
                    )
                    return 1

                row = result.to_json_obj()
                row["suite_version"] = suite.suite_version
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(row)
                print(
                    f"run {run_idx}/{total_runs} task={task.task_id} seed={seed} "
                    f"outcome={result.outcome} reason={result.reason} ticks={result.ticks}"
                )

    if not args.no_summary:
        summary = summarize_episode_rows(rows)
        print(
            f"\nSuite {suite.suite_id} v{suite.suite_version}: "
            f"{summary['episodes']} episodes, success_rate={summary['success_rate']:.1%}"
        )
        for tid, stats in sorted(summary["by_task"].items()):
            mt = stats.get("mean_ticks")
            mt_s = f" mean_ticks={mt:.0f}" if isinstance(mt, float) else ""
            print(
                f"  {tid}: {stats['success_rate']:.0%} success "
                f"({stats['successes']}/{stats['episodes']}){mt_s}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
