"""Benchmark suite loading and aggregate metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SuiteTask:
    task_id: str
    task_spec: dict[str, Any]
    scenario_id: str | None
    skill_family: str | None
    tags: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkSuite:
    suite_id: str
    suite_version: str
    description: str
    default_scenario_id: str
    episodes_per_task: int
    seed_base: int
    tasks: tuple[SuiteTask, ...]
    path: Path


def load_task_spec_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: expected JSON object")
    return obj


def load_suite(path: Path) -> BenchmarkSuite:
    root = path.resolve().parent
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: suite root must be a JSON object")

    suite_id = str(raw.get("suite_id", "")).strip()
    if not suite_id:
        raise ValueError(f"{path}: missing suite_id")

    tasks_raw = raw.get("tasks")
    if not isinstance(tasks_raw, list) or not tasks_raw:
        raise ValueError(f"{path}: tasks must be a non-empty array")

    default_scenario = str(raw.get("default_scenario_id", "ZombieRoom-v0"))
    episodes = int(raw.get("episodes_per_task", 1))
    seed_base = int(raw.get("seed_base", 0))
    if episodes < 1:
        raise ValueError(f"{path}: episodes_per_task must be >= 1")

    tasks: list[SuiteTask] = []
    for i, entry in enumerate(tasks_raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: tasks[{i}] must be an object")
        task_id = str(entry.get("task_id", "")).strip()
        if not task_id:
            raise ValueError(f"{path}: tasks[{i}] missing task_id")

        if "task_spec" in entry:
            spec = entry["task_spec"]
            if not isinstance(spec, dict):
                raise ValueError(f"{path}: tasks[{i}].task_spec must be an object")
            task_spec = dict(spec)
        elif "task_spec_file" in entry:
            rel = str(entry["task_spec_file"])
            spec_path = (root / rel).resolve()
            task_spec = load_task_spec_json(spec_path)
        else:
            raise ValueError(f"{path}: tasks[{i}] needs task_spec or task_spec_file")

        scenario_id = entry.get("scenario_id")
        scenario = str(scenario_id).strip() if scenario_id is not None else None
        if scenario == "":
            scenario = None

        skill = entry.get("skill_family")
        skill_family = str(skill).strip() if skill is not None else None
        if skill_family == "":
            skill_family = None

        tags_raw = entry.get("tags", [])
        if tags_raw is None:
            tags_raw = []
        if not isinstance(tags_raw, list):
            raise ValueError(f"{path}: tasks[{i}].tags must be an array")
        tags = tuple(str(t) for t in tags_raw)

        tasks.append(
            SuiteTask(
                task_id=task_id,
                task_spec=task_spec,
                scenario_id=scenario,
                skill_family=skill_family,
                tags=tags,
            )
        )

    return BenchmarkSuite(
        suite_id=suite_id,
        suite_version=str(raw.get("suite_version", "1")),
        description=str(raw.get("description", "")),
        default_scenario_id=default_scenario,
        episodes_per_task=episodes,
        seed_base=seed_base,
        tasks=tuple(tasks),
        path=path,
    )


def filter_tasks(
    suite: BenchmarkSuite,
    *,
    task_ids: set[str] | None = None,
    tags: set[str] | None = None,
) -> tuple[SuiteTask, ...]:
    out: list[SuiteTask] = []
    for task in suite.tasks:
        if task_ids is not None and task.task_id not in task_ids:
            continue
        if tags is not None and not tags.intersection(task.tags):
            continue
        out.append(task)
    return tuple(out)


def summarize_episode_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate JSONL episode rows (already parsed dicts)."""
    if not rows:
        return {"episodes": 0, "success_rate": 0.0, "by_task": {}}

    successes = sum(1 for r in rows if r.get("outcome") == "success")
    by_task: dict[str, dict[str, Any]] = {}

    for row in rows:
        tid = str(row.get("task_id") or row.get("scenario_id") or "unknown")
        bucket = by_task.setdefault(
            tid,
            {
                "episodes": 0,
                "successes": 0,
                "failures": 0,
                "timeouts": 0,
                "ticks": [],
                "skill_family": row.get("skill_family"),
            },
        )
        bucket["episodes"] += 1
        outcome = row.get("outcome")
        if outcome == "success":
            bucket["successes"] += 1
        elif outcome == "timeout":
            bucket["timeouts"] += 1
        elif outcome == "failure":
            bucket["failures"] += 1
        ticks = row.get("ticks")
        if isinstance(ticks, int):
            bucket["ticks"].append(ticks)

    for bucket in by_task.values():
        eps = bucket["episodes"]
        bucket["success_rate"] = bucket["successes"] / eps if eps else 0.0
        ts = bucket.pop("ticks")
        bucket["mean_ticks"] = sum(ts) / len(ts) if ts else None

    return {
        "episodes": len(rows),
        "success_rate": successes / len(rows),
        "by_task": by_task,
    }
