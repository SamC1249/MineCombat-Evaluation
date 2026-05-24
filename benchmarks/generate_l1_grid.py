#!/usr/bin/env python3
"""
Generate the Level 1 task_spec grid under benchmarks/l1-v1/.

Grid: mob × gear tier × time-of-day on the template arena (ZombieRoom-v0 base).
Regenerate after editing MOBS, GEAR_TIERS, or TIMES below.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "benchmarks" / "l1-v1"
TASKS_DIR = OUT_DIR / "tasks"

# Curated mobs — skill families for benchmark reporting.
MOBS: tuple[tuple[str, str], ...] = (
    ("ZOMBIE", "baseline_melee"),
    ("CREEPER", "explosion_pressure"),
    ("SKELETON", "ranged_kiting"),
    ("SPIDER", "fast_melee"),
    ("ENDERMAN", "teleport_melee"),
    ("WITCH", "potion_ranged"),
)

GEAR_TIERS: dict[str, dict[str, str]] = {
    "wood": {"weapon": "WOODEN_SWORD"},
    "stone": {"weapon": "STONE_SWORD"},
    "iron_full": {
        "weapon": "IRON_SWORD",
        "helmet": "IRON_HELMET",
        "chestplate": "IRON_CHESTPLATE",
        "leggings": "IRON_LEGGINGS",
        "boots": "IRON_BOOTS",
    },
}

TIMES: tuple[str, ...] = ("day", "night")

MAX_TICKS = 2400
SCENARIO_VERSION = "1"


def task_id(entity: str, gear: str, time_of_day: str) -> str:
    return f"{entity.lower()}_{gear}_{time_of_day}"


def build_task_spec(entity: str, gear: str, time_of_day: str) -> dict[str, object]:
    return {
        "entity": entity,
        "time_of_day": time_of_day,
        "max_ticks": MAX_TICKS,
        "scenario_version": SCENARIO_VERSION,
        "gear": dict(GEAR_TIERS[gear]),
    }


def main() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    for old in TASKS_DIR.glob("*.json"):
        old.unlink()

    suite_tasks: list[dict[str, object]] = []
    for entity, skill in MOBS:
        for gear in GEAR_TIERS:
            for tod in TIMES:
                tid = task_id(entity, gear, tod)
                spec = build_task_spec(entity, gear, tod)
                rel = f"tasks/{tid}.json"
                (TASKS_DIR / f"{tid}.json").write_text(
                    json.dumps(spec, indent=2) + "\n",
                    encoding="utf-8",
                )
                tags = ["core", f"gear_{gear}", f"time_{tod}", f"mob_{entity.lower()}"]
                suite_tasks.append(
                    {
                        "task_id": tid,
                        "skill_family": skill,
                        "tags": tags,
                        "task_spec_file": rel,
                    }
                )

    suite = {
        "suite_id": "l1-v1",
        "suite_version": "1",
        "description": (
            "Level 1 task_spec grid: 6 mobs × 3 gear tiers × day/night on the "
            "template arena. Base scenario ZombieRoom-v0; overrides via task_spec."
        ),
        "default_scenario_id": "ZombieRoom-v0",
        "episodes_per_task": 1,
        "seed_base": 0,
        "tasks": suite_tasks,
    }
    (OUT_DIR / "suite.json").write_text(
        json.dumps(suite, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(suite_tasks)} tasks to {TASKS_DIR}")
    print(f"Suite manifest: {OUT_DIR / 'suite.json'}")


if __name__ == "__main__":
    main()
