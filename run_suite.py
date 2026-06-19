#!/usr/bin/env python3
"""Thin CLI shim over minecombat_eval.runner (logic now lives in the package).

Example:
  python3 run_suite.py --suite benchmarks/l1-v1/suite.json -o results/l1-v1.jsonl
"""

from __future__ import annotations

import argparse
from pathlib import Path

from minecombat_eval.runner import run_suite


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a MineCombat benchmark suite over TCP.")
    p.add_argument("--suite", type=Path, required=True)
    p.add_argument("--tasks", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--episodes", type=int, default=None, metavar="N")
    p.add_argument("--seed-base", type=int, default=None, metavar="K")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("-o", "--output", type=Path, default=Path("episodes.jsonl"))
    p.add_argument("--agent", choices=("noop", "random"), default="noop")
    p.add_argument("--agent-seed", type=int, default=None)
    p.add_argument("--policy", default=None, metavar="module:attr")
    p.add_argument("--no-summary", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = _parse_args(argv)
    return run_suite(
        suite_path=a.suite,
        tasks=a.tasks,
        tags=a.tags,
        episodes=a.episodes,
        seed_base=a.seed_base,
        host=a.host,
        port=a.port,
        output=a.output,
        agent=a.agent,
        agent_seed=a.agent_seed,
        policy=a.policy,
        no_summary=a.no_summary,
    )


if __name__ == "__main__":
    raise SystemExit(main())
