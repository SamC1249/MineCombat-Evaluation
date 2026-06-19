#!/usr/bin/env python3
"""Thin CLI shim over minecombat_eval.runner (logic now lives in the package).

Kept for repo-root usage: `python3 run_eval.py --scenario ZombieRoom-v0`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# Re-exported for backward compatibility with code that imported from run_eval.
from minecombat_eval.loader import load_policy_entry  # noqa: F401
from minecombat_eval.runner import (  # noqa: F401
    eprint_eval_failure as _eprint_eval_failure,
    run_eval,
    run_one_episode,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run MineCombat-Evaluation episodes over TCP and log to JSONL."
    )
    p.add_argument("--scenario", default="ZombieRoom-v0")
    p.add_argument("--episodes", type=int, default=1, metavar="N")
    p.add_argument("--seed-base", type=int, default=0, metavar="K")
    p.add_argument("--seed", type=int, default=None, metavar="S")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("-o", "--output", type=Path, default=Path("episodes.jsonl"))
    p.add_argument("--agent", choices=("noop", "random"), default="noop")
    p.add_argument("--agent-seed", type=int, default=None, metavar="R")
    p.add_argument("--policy", default=None, metavar="module:attr")
    p.add_argument("--task-json", type=Path, default=None, metavar="FILE")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = _parse_args(argv)
    return run_eval(
        scenario=a.scenario,
        episodes=a.episodes,
        seed_base=a.seed_base,
        seed=a.seed,
        host=a.host,
        port=a.port,
        output=a.output,
        agent=a.agent,
        agent_seed=a.agent_seed,
        policy=a.policy,
        task_json=a.task_json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
