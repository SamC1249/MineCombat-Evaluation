#!/usr/bin/env python3
"""Generate benchmark suite manifests for Level 2 cave and beach environments."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MOB_SUFFIXES = [
    "",
    "-creeper",
    "-skeleton",
    "-enderman",
    "-spider",
    "-baby-zombie",
    "-witch",
    "-magma-cube",
    "-slime",
    "-hoglin",
    "-silverfish",
    "-blaze",
    "-shulker",
]
GEAR_SUFFIXES = [
    "L1-wood-night",
    "L1-stone-day",
    "L1-iron-leather-day",
    "L1-iron-full-day",
]


def task_entries(prefix: str) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for suffix in MOB_SUFFIXES:
        sid = f"{prefix}-v0{suffix}"
        tid = sid.replace(f"{prefix}-", "").lower().replace("-", "_")
        tasks.append(
            {
                "task_id": tid,
                "scenario_id": sid,
                "skill_family": "l2_combat",
                "tags": ["core", "l2", prefix.split("Room")[0].lower()],
            }
        )
    for suffix in GEAR_SUFFIXES:
        sid = f"{prefix}-{suffix}"
        tid = sid.replace(f"{prefix}-", "").lower().replace("-", "_")
        tasks.append(
            {
                "task_id": tid,
                "scenario_id": sid,
                "skill_family": "l2_combat",
                "tags": ["core", "l2", "gear", prefix.split("Room")[0].lower()],
            }
        )
    return tasks


def write_suite(env_name: str, prefix: str) -> None:
    out_dir = REPO_ROOT / "benchmarks" / f"l2-{env_name}-v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    suite = {
        "suite_id": f"l2-{env_name}-v1",
        "suite_version": "1",
        "description": f"Level 2 {env_name} environment — 17 scenarios (13 mobs + 4 gear/time).",
        "default_scenario_id": f"{prefix}-v0",
        "episodes_per_task": 1,
        "seed_base": 0,
        "tasks": task_entries(prefix),
    }
    (out_dir / "suite.json").write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir / 'suite.json'} ({len(suite['tasks'])} tasks)")


def main() -> None:
    write_suite("cave", "CaveRoom")
    write_suite("beach", "BeachRoom")


if __name__ == "__main__":
    main()
