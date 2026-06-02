"""CLI for bootstrap, eval runs, and result summaries."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .bootstrap import BootstrapError, bootstrap, export_world, load_manifest, repo_root


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
