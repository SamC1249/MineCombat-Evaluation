"""CLI for bootstrap, server start, eval runs, and result summaries.

Works from a plain ``pip install minecombat-eval`` (no repo checkout): bundled
plugin/config/world/suites are used, and the server JRE is auto-provisioned.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

from .bootstrap import (
    BootstrapError,
    bootstrap,
    bundled_suite_path,
    export_world,
    load_manifest,
    repo_root,
    start_server,
)
from .helpers import validate_action
from .loader import load_policy_entry
from .scaffold import KINDS, ScaffoldError, init_policy
from .synthetic import approach_episode


def _load_dotenv() -> None:
    env_path = repo_root() / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _suite_path(name: str) -> Path:
    bundled = bundled_suite_path(name)
    if bundled is not None:
        return bundled
    manifest = load_manifest()
    suites = manifest.get("suites", {})
    if name in suites:
        return repo_root() / suites[name]
    p = Path(name)
    if p.is_file():
        return p
    candidate = repo_root() / "benchmarks" / name / "suite.json"
    if candidate.is_file():
        return candidate
    raise BootstrapError(f"unknown suite {name!r}; known: {', '.join(sorted(suites))}")


def cmd_bootstrap(args: argparse.Namespace) -> int:
    try:
        bootstrap(
            server=args.server,
            skip_build=args.skip_build,
            skip_paper=args.skip_paper,
            skip_world=args.skip_world,
            force_world=args.force_world,
            force_paper=args.force_paper,
            online_mode=not args.offline,
        )
    except (BootstrapError, subprocess.CalledProcessError) as e:
        print(f"bootstrap: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_export_world(args: argparse.Namespace) -> int:
    try:
        source = Path(args.source).resolve() if args.source else None
        export_world(source=source, server=args.server)
    except BootstrapError as e:
        print(f"export-world: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_run_eval(args: argparse.Namespace) -> int:
    from .runner import run_eval

    return run_eval(
        scenario=args.scenario,
        episodes=args.episodes,
        seed_base=args.seed_base,
        host=args.host,
        port=args.port,
        output=args.output or "episodes.jsonl",
        agent=args.agent or "noop",
        policy=args.policy,
    )


def cmd_run_suite(args: argparse.Namespace) -> int:
    from .runner import run_suite

    try:
        suite = _suite_path(args.suite)
    except BootstrapError as e:
        print(str(e), file=sys.stderr)
        return 2
    return run_suite(
        suite_path=suite,
        tasks=args.tasks,
        tags=args.tags,
        episodes=args.episodes,
        seed_base=args.seed_base,
        host=args.host,
        port=args.port,
        output=args.output or "episodes.jsonl",
        agent=args.agent or "noop",
        policy=args.policy,
    )


def cmd_summarize(args: argparse.Namespace) -> int:
    from .suite import summarize_episode_rows

    rows: list[dict] = []
    for path in args.inputs:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    summary = summarize_episode_rows(rows)
    print(f"episodes={summary['episodes']} success_rate={summary['success_rate']:.1%}")
    for tid, stats in sorted(summary["by_task"].items()):
        print(f"  {tid}: {stats['success_rate']:.0%} ({stats['successes']}/{stats['episodes']})")
    if args.csv:
        import csv

        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["task_id", "episodes", "successes", "success_rate", "mean_ticks"])
            for tid, stats in sorted(summary["by_task"].items()):
                w.writerow([tid, stats["episodes"], stats["successes"],
                            f"{stats['success_rate']:.4f}", stats.get("mean_ticks")])
        print(f"wrote {args.csv}")
    return 0


def cmd_server_start(args: argparse.Namespace) -> int:
    try:
        return start_server(
            server=args.server,
            java_version=args.java_version,
            allow_download=not args.no_download,
            memory=args.memory,
        )
    except BootstrapError as e:
        print(f"server start: {e}", file=sys.stderr)
        return 1


def cmd_init_policy(args: argparse.Namespace) -> int:
    directory = Path(args.dir).resolve() if args.dir else None
    try:
        pkg_dir, spec = init_policy(args.name, kind=args.kind, directory=directory)
    except ScaffoldError as e:
        print(f"init-policy: {e}", file=sys.stderr)
        return 2
    rel = os.path.relpath(pkg_dir)
    print(f"created {rel}/ ({args.kind} policy)")
    print("next:")
    print(f"  minecombat-eval test-policy {spec}      # validate offline (no Minecraft)")
    print(f"  minecombat-eval run-eval --policy {spec} # run against a live server")
    return 0


def cmd_test_policy(args: argparse.Namespace) -> int:
    """Import a policy and run it on synthetic observations; no server needed."""
    try:
        agent_fn, before = load_policy_entry(args.policy)
    except (ImportError, ValueError, TypeError, AttributeError) as e:
        print(f"test-policy: could not load {args.policy!r}: {e}", file=sys.stderr)
        return 2

    if before is not None:
        try:
            before({"scenario_id": args.scenario, "seed": 0})
        except Exception as e:  # noqa: BLE001 - report any user reset() failure
            print(f"test-policy: reset() raised {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc()
            return 1

    ran = 0
    invalid_ticks: list[tuple[int, list[str]]] = []
    samples: list[str] = []
    for obs in approach_episode(args.ticks, scenario_id=args.scenario):
        tick = obs["tick"]
        try:
            action = agent_fn(obs, tick)
        except Exception as e:  # noqa: BLE001 - surface the policy's own error
            print(f"test-policy: act() raised at tick {tick}: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc()
            return 1
        ran += 1
        problems = validate_action(action)
        if problems:
            invalid_ticks.append((tick, problems))
        if tick in (0, args.ticks // 2, args.ticks - 1):
            samples.append(f"  tick {tick:>3}: {action}")

    print(f"loaded {args.policy}")
    print(f"ran act() on {ran} synthetic ticks (mob approaching player)")
    if samples:
        print("sample actions:")
        print("\n".join(samples))
    if invalid_ticks:
        print(f"\nFAIL: {len(invalid_ticks)} tick(s) returned an invalid action:", file=sys.stderr)
        for tick, problems in invalid_ticks[:5]:
            print(f"  tick {tick}: {'; '.join(problems)}", file=sys.stderr)
        return 1
    print("\nOK: policy imports, runs, and returns valid actions.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="minecombat-eval",
        description="MineCombat-Evaluation bootstrap and eval CLI",
    )
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bootstrap", help="Download Paper + JRE deps, install bundled plugin/world/config")
    b.add_argument("--server", help="Paper server directory (default: $SERVER or ~/minecraft-paper-mcbench)")
    b.add_argument("--skip-build", action="store_true", help="Reuse existing plugin JAR if present")
    b.add_argument("--skip-paper", action="store_true", help="Do not download paper.jar")
    b.add_argument("--skip-world", action="store_true", help="Do not install mcbench_flat world")
    b.add_argument("--force-world", action="store_true", help="Replace existing world folder")
    b.add_argument("--force-paper", action="store_true", help="Re-download paper.jar")
    b.add_argument("--offline", action="store_true", help="Set online-mode=false for frictionless local join")
    b.set_defaults(func=cmd_bootstrap)

    ew = sub.add_parser("export-world", help="Export world zip from SERVER (maintainers)")
    ew.add_argument("--server", help="Paper server directory")
    ew.add_argument("--source", help="Path to world folder (overrides --server)")
    ew.set_defaults(func=cmd_export_world)

    re = sub.add_parser("run-eval", help="Run episodes against a running server")
    re.add_argument("--scenario", default="ZombieRoom-v0")
    re.add_argument("--episodes", type=int, default=1)
    re.add_argument("--seed-base", type=int, default=0)
    re.add_argument("--policy", default=None)
    re.add_argument("--agent", choices=("noop", "random"), default=None)
    re.add_argument("-o", "--output", default=None)
    re.add_argument("--host", default="127.0.0.1")
    re.add_argument("--port", type=int, default=8765)
    re.set_defaults(func=cmd_run_eval)

    rs = sub.add_parser("run-suite", help="Run benchmark suite by id or path")
    rs.add_argument("suite", help="Suite id (l1-v1, l2-cave-v1, …) or path to suite.json")
    rs.add_argument("--episodes", type=int, default=None)
    rs.add_argument("--seed-base", type=int, default=None)
    rs.add_argument("--policy", default="minecombat_eval.reference_policy:ReferenceCombatPolicy")
    rs.add_argument("--agent", choices=("noop", "random"), default=None)
    rs.add_argument("-o", "--output", default=None)
    rs.add_argument("--host", default="127.0.0.1")
    rs.add_argument("--port", type=int, default=8765)
    rs.add_argument("--tasks", default="")
    rs.add_argument("--tags", default="")
    rs.set_defaults(func=cmd_run_suite)

    ip = sub.add_parser("init-policy", help="Scaffold a custom policy package you can edit and run")
    ip.add_argument("name", help="Package name (Python identifier, e.g. my_agent)")
    ip.add_argument("--kind", choices=KINDS, default="conditional", help="Template (default: conditional)")
    ip.add_argument("--dir", default=None, help="Parent directory for the package (default: cwd)")
    ip.set_defaults(func=cmd_init_policy)

    tp = sub.add_parser(
        "test-policy",
        help="Validate a policy on synthetic observations offline (no Minecraft needed)",
    )
    tp.add_argument("policy", help="module:Class or module:callable, e.g. my_agent.policy:MyAgentPolicy")
    tp.add_argument("--ticks", type=int, default=60, help="Synthetic ticks to run (default: 60)")
    tp.add_argument("--scenario", default="ZombieRoom-v0", help="scenario_id put in the fake observation")
    tp.set_defaults(func=cmd_test_policy)

    sm = sub.add_parser("summarize", help="Summarize JSONL eval logs")
    sm.add_argument("inputs", nargs="+", type=Path)
    sm.add_argument("--csv", type=Path, default=None)
    sm.set_defaults(func=cmd_summarize)

    ss = sub.add_parser("server", help="Paper server helpers")
    ss_sub = ss.add_subparsers(dest="server_cmd", required=True)
    start = ss_sub.add_parser("start", help="Start Paper (auto-provisions a JRE)")
    start.add_argument("--server", default=None)
    start.add_argument("--java-version", type=int, default=25, help="Required Java major version (default 25)")
    start.add_argument("--no-download", action="store_true", help="Fail instead of downloading a JRE")
    start.add_argument("--memory", default="2G", help="Heap size for -Xms/-Xmx (default 2G)")
    start.set_defaults(func=cmd_server_start)

    return p


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    os.environ.setdefault("MINECOMBAT_EVAL_ROOT", str(repo_root()))
    # Make policies in the user's working directory importable (e.g. my_agent.policy).
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
