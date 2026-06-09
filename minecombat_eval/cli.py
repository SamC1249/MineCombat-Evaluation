"""CLI for bootstrap, eval runs, and result summaries."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import traceback
from pathlib import Path

from .bootstrap import BootstrapError, bootstrap, export_world, load_manifest, repo_root
from .helpers import validate_action
from .loader import load_policy_entry
from .scaffold import KINDS, ScaffoldError, init_policy
from .synthetic import approach_episode


def _load_dotenv() -> None:
    root = repo_root()
    env_path = root / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def _suite_path(name: str) -> Path:
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
    root = repo_root()
    argv = [sys.executable, str(root / "run_eval.py")]
    if args.scenario:
        argv.extend(["--scenario", args.scenario])
    if args.episodes is not None:
        argv.extend(["--episodes", str(args.episodes)])
    if args.seed_base is not None:
        argv.extend(["--seed-base", str(args.seed_base)])
    if args.policy:
        argv.extend(["--policy", args.policy])
    if args.agent:
        argv.extend(["--agent", args.agent])
    if args.output:
        argv.extend(["-o", args.output])
    if args.host:
        argv.extend(["--host", args.host])
    if args.port is not None:
        argv.extend(["--port", str(args.port)])
    if args.extra:
        argv.extend(args.extra)
    return subprocess.call(argv, cwd=root)


def cmd_run_suite(args: argparse.Namespace) -> int:
    root = repo_root()
    try:
        suite = _suite_path(args.suite)
    except BootstrapError as e:
        print(str(e), file=sys.stderr)
        return 2
    argv = [str(root / "run_suite.py"), "--suite", str(suite)]
    if args.episodes is not None:
        argv.extend(["--episodes", str(args.episodes)])
    if args.seed_base is not None:
        argv.extend(["--seed-base", str(args.seed_base)])
    if args.policy:
        argv.extend(["--policy", args.policy])
    if args.agent:
        argv.extend(["--agent", args.agent])
    if args.output:
        argv.extend(["-o", args.output])
    if args.host:
        argv.extend(["--host", args.host])
    if args.port is not None:
        argv.extend(["--port", str(args.port)])
    if args.tasks:
        argv.extend(["--tasks", args.tasks])
    if args.tags:
        argv.extend(["--tags", args.tags])
    argv.extend(args.extra)
    return subprocess.call([sys.executable, *argv], cwd=root)


def cmd_summarize(args: argparse.Namespace) -> int:
    root = repo_root()
    script = root / "scripts" / "summarize_results.py"
    argv = [sys.executable, str(script), *[str(p) for p in args.inputs]]
    if args.csv:
        argv.extend(["--csv", str(args.csv)])
    return subprocess.call(argv, cwd=root)


def cmd_server_start(args: argparse.Namespace) -> int:
    root = repo_root()
    script = root / "scripts" / "run-paper.sh"
    if not script.is_file():
        print("run-paper.sh not found; clone repo or set MINECOMBAT_EVAL_ROOT", file=sys.stderr)
        return 1
    if args.server:
        os.environ["SERVER"] = args.server
    return subprocess.call([str(script)], cwd=root)


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

    b = sub.add_parser("bootstrap", help="Download Paper, build plugin, install world + config")
    b.add_argument("--server", help="Paper server directory (default: $SERVER or ~/minecraft-paper-mcbench)")
    b.add_argument("--skip-build", action="store_true", help="Reuse existing plugin JAR if present")
    b.add_argument("--skip-paper", action="store_true", help="Do not download paper.jar")
    b.add_argument("--skip-world", action="store_true", help="Do not install mcbench_flat world")
    b.add_argument("--force-world", action="store_true", help="Replace existing world folder")
    b.add_argument("--force-paper", action="store_true", help="Re-download paper.jar")
    b.set_defaults(func=cmd_bootstrap)

    ew = sub.add_parser("export-world", help="Export world zip from SERVER (maintainers)")
    ew.add_argument("--server", help="Paper server directory")
    ew.add_argument("--source", help="Path to world folder (overrides --server)")
    ew.set_defaults(func=cmd_export_world)

    re = sub.add_parser("run-eval", help="Run episodes (wraps run_eval.py)")
    re.add_argument("--scenario", default="ZombieRoom-v0")
    re.add_argument("--episodes", type=int, default=1)
    re.add_argument("--seed-base", type=int, default=0)
    re.add_argument("--policy", default=None)
    re.add_argument("--agent", choices=("noop", "random"), default=None)
    re.add_argument("-o", "--output", default=None)
    re.add_argument("--host", default="127.0.0.1")
    re.add_argument("--port", type=int, default=8765)
    re.add_argument("extra", nargs=argparse.REMAINDER, help="Extra args passed to run_eval.py")
    re.set_defaults(func=cmd_run_eval)

    rs = sub.add_parser("run-suite", help="Run benchmark suite by id or path")
    rs.add_argument("suite", help="Suite id (l1-v1, l2-cave-v1, …) or path to suite.json")
    rs.add_argument("--episodes", type=int, default=10)
    rs.add_argument("--seed-base", type=int, default=0)
    rs.add_argument(
        "--policy",
        default="minecombat_eval.reference_policy:ReferenceCombatPolicy",
    )
    rs.add_argument("--agent", choices=("noop", "random"), default=None)
    rs.add_argument("-o", "--output", default=None)
    rs.add_argument("--host", default="127.0.0.1")
    rs.add_argument("--port", type=int, default=8765)
    rs.add_argument("--tasks", default="")
    rs.add_argument("--tags", default="")
    rs.add_argument("extra", nargs=argparse.REMAINDER)
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
    start = ss_sub.add_parser("start", help="Start Paper (requires JAVA_25 + SERVER)")
    start.add_argument("--server", default=None)
    start.set_defaults(func=cmd_server_start)

    return p


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    os.environ.setdefault("MINECOMBAT_EVAL_ROOT", str(repo_root()))
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
