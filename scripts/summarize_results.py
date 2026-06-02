#!/usr/bin/env python3
"""Summarize JSONL eval logs into terminal tables and optional CSV."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_rows(paths: list[Path]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        with path.open(encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path}:{line_no}: invalid JSON: {e}") from e
                if not isinstance(obj, dict):
                    raise ValueError(f"{path}:{line_no}: expected JSON object")
                rows.append((path.name, obj))
    return rows


def _group_key(row: dict[str, Any]) -> str:
    tid = row.get("task_id")
    if tid:
        return str(tid)
    return str(row.get("scenario_id") or "unknown")


def _stats_for_group(items: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(items)
    outcomes = [str(r.get("outcome") or "") for r in items]
    successes = sum(1 for o in outcomes if o == "success")
    failures = sum(1 for o in outcomes if o == "failure")
    timeouts = sum(1 for o in outcomes if o == "timeout")
    ticks = [int(r["ticks"]) for r in items if isinstance(r.get("ticks"), int)]
    mean_ticks = sum(ticks) / len(ticks) if ticks else None
    std_ticks = None
    if len(ticks) > 1 and mean_ticks is not None:
        var = sum((t - mean_ticks) ** 2 for t in ticks) / (len(ticks) - 1)
        std_ticks = math.sqrt(var)
    suite_id = next((r.get("suite_id") for r in items if r.get("suite_id")), None)
    return {
        "episodes": n,
        "success_rate": successes / n if n else 0.0,
        "failure_rate": failures / n if n else 0.0,
        "timeout_rate": timeouts / n if n else 0.0,
        "mean_ticks": mean_ticks,
        "std_ticks": std_ticks,
        "suite_id": suite_id,
    }


def summarize(rows: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fname, row in rows:
        by_file[fname].append(row)
        by_task[_group_key(row)].append(row)

    all_objs = [r for _, r in rows]
    overall = _stats_for_group(all_objs) if all_objs else _stats_for_group([])
    return {
        "overall": overall,
        "by_file": {f: _stats_for_group(rs) for f, rs in sorted(by_file.items())},
        "by_task": {k: _stats_for_group(rs) for k, rs in sorted(by_task.items())},
    }


def _pct(v: float) -> str:
    return f"{100.0 * v:.1f}%"


def _fmt_ticks(mean: float | None, std: float | None) -> str:
    if mean is None:
        return "-"
    if std is None:
        return f"{mean:.0f}"
    return f"{mean:.0f}±{std:.0f}"


def print_table(title: str, groups: dict[str, dict[str, Any]]) -> None:
    print(f"\n{title}")
    header = (
        f"{'group':<28} {'eps':>5} {'success':>8} {'fail':>8} "
        f"{'timeout':>8} {'mean_ticks':>12}"
    )
    print(header)
    print("-" * len(header))
    for name, s in groups.items():
        print(
            f"{name:<28} {s['episodes']:>5} {_pct(s['success_rate']):>8} "
            f"{_pct(s['failure_rate']):>8} {_pct(s['timeout_rate']):>8} "
            f"{_fmt_ticks(s['mean_ticks'], s['std_ticks']):>12}"
        )


def write_csv(path: Path, groups: dict[str, dict[str, Any]], *, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                label,
                "episodes",
                "success_rate",
                "failure_rate",
                "timeout_rate",
                "mean_ticks",
                "std_ticks",
                "suite_id",
            ]
        )
        for name, s in groups.items():
            w.writerow(
                [
                    name,
                    s["episodes"],
                    f"{s['success_rate']:.4f}",
                    f"{s['failure_rate']:.4f}",
                    f"{s['timeout_rate']:.4f}",
                    "" if s["mean_ticks"] is None else f"{s['mean_ticks']:.2f}",
                    "" if s["std_ticks"] is None else f"{s['std_ticks']:.2f}",
                    s.get("suite_id") or "",
                ]
            )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Summarize MineCombat JSONL eval logs.")
    p.add_argument("inputs", nargs="+", type=Path, help="One or more .jsonl files")
    p.add_argument("--csv", type=Path, default=None, help="Write per-task CSV to PATH")
    args = p.parse_args(argv)

    paths = [p.resolve() for p in args.inputs]
    for path in paths:
        if not path.is_file():
            print(f"missing file: {path}", file=sys.stderr)
            return 2

    try:
        rows = _load_rows(paths)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    if not rows:
        print("No episode rows found.", file=sys.stderr)
        return 2

    summary = summarize(rows)
    o = summary["overall"]
    print(
        f"Total: {o['episodes']} episodes, success={_pct(o['success_rate'])}, "
        f"fail={_pct(o['failure_rate'])}, timeout={_pct(o['timeout_rate'])}, "
        f"ticks={_fmt_ticks(o['mean_ticks'], o['std_ticks'])}"
    )
    print_table("By file", summary["by_file"])
    print_table("By task/scenario", summary["by_task"])

    if args.csv:
        write_csv(args.csv, summary["by_task"], label="task_id")
        print(f"\nWrote CSV: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
