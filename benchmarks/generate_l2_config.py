#!/usr/bin/env python3
"""
Append Level 2 environment templates + mob/gear scenarios to plugin config.yml.

Regenerate after editing ENVIRONMENTS or MOB_VARIANTS below.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "paper-plugin" / "src" / "main" / "resources" / "config.yml"

ENVIRONMENTS_YAML = """
  # Level 2 custom-built arenas (unique spawn per environment).
  environments:
    cave:
      spawn:
        player: { x: -50.0, y: -58.0, z: 34.0, yaw: 0.0, pitch: 0.0 }
        hostile: { x: -44.0, y: -58.0, z: 30.0 }
      arena:
        center-x: -47.0
        center-y: -58.0
        center-z: 32.0
        half-size: 16
        mob-clear-half-size: 48
        min-y-delta: 6
        max-y-delta: 10
    beach:
      spawn:
        player: { x: -16.0, y: 61.0, z: 27.0, yaw: 0.0, pitch: 0.0 }
        hostile: { x: -12.0, y: 61.0, z: 32.0 }
      arena:
        center-x: -14.0
        center-y: 61.0
        center-z: 29.5
        half-size: 16
        mob-clear-half-size: 48
        min-y-delta: 4
        max-y-delta: 8
"""

MOB_VARIANTS: list[tuple[str, str, bool]] = [
    ("", "ZOMBIE", False),
    ("-creeper", "CREEPER", False),
    ("-skeleton", "SKELETON", False),
    ("-enderman", "ENDERMAN", False),
    ("-spider", "SPIDER", False),
    ("-baby-zombie", "ZOMBIE", True),
    ("-witch", "WITCH", False),
    ("-magma-cube", "MAGMA_CUBE", False),
    ("-slime", "SLIME", False),
    ("-hoglin", "HOGLIN", False),
    ("-silverfish", "SILVERFISH", False),
    ("-blaze", "BLAZE", False),
    ("-shulker", "SHULKER", False),
]

GEAR_VARIANTS: list[tuple[str, dict[str, object]]] = [
    ("L1-wood-night", {"time-of-day": "night", "gear": {"weapon": "WOODEN_SWORD"}}),
    ("L1-stone-day", {"time-of-day": "day", "gear": {"weapon": "STONE_SWORD"}}),
    (
        "L1-iron-leather-day",
        {
            "time-of-day": "day",
            "gear": {
                "weapon": "IRON_SWORD",
                "helmet": "LEATHER_HELMET",
                "chestplate": "LEATHER_CHESTPLATE",
                "leggings": "LEATHER_LEGGINGS",
                "boots": "LEATHER_BOOTS",
            },
        },
    ),
    (
        "L1-iron-full-day",
        {
            "time-of-day": "day",
            "gear": {
                "weapon": "IRON_SWORD",
                "helmet": "IRON_HELMET",
                "chestplate": "IRON_CHESTPLATE",
                "leggings": "IRON_LEGGINGS",
                "boots": "IRON_BOOTS",
            },
        },
    ),
]

ENV_PREFIX = {"cave": "CaveRoom", "beach": "BeachRoom"}


def scenario_yaml(
    scenario_id: str,
    environment: str,
    *,
    entity: str | None = None,
    baby: bool = False,
    extra: dict[str, object] | None = None,
) -> str:
    lines = [
        f"    {scenario_id}:",
        "      level: 2",
        '      scenario-version: "1"',
        "      max-ticks: 2400",
        f"      environment: {environment}",
    ]
    if extra and "time-of-day" in extra:
        lines.append(f"      time-of-day: {extra['time-of-day']}")
    else:
        lines.append("      time-of-day: day")
    if entity:
        lines.append(f"      entity: {entity}")
    if baby:
        lines.append("      baby: true")
    lines.append("      gear:")
    if extra and "gear" in extra:
        gear = extra["gear"]
        assert isinstance(gear, dict)
        for slot, mat in gear.items():
            lines.append(f"        {slot}: {mat}")
    else:
        lines.append("        weapon: WOODEN_SWORD")
    return "\n".join(lines)


def build_l2_scenarios_yaml() -> str:
    blocks: list[str] = []
    for env_key, prefix in ENV_PREFIX.items():
        for suffix, entity, baby in MOB_VARIANTS:
            sid = f"{prefix}-v0{suffix}"
            blocks.append(scenario_yaml(sid, env_key, entity=entity, baby=baby))
        for suffix, extra in GEAR_VARIANTS:
            sid = f"{prefix}-{suffix}"
            blocks.append(scenario_yaml(sid, env_key, entity="ZOMBIE", extra=extra))
    return "\n".join(blocks)


def strip_l2_scenarios(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        if re.match(r"    (CaveRoom|BeachRoom)-", line):
            skip = True
            continue
        if skip:
            if re.match(r"    [A-Za-z].*:", line) and not line.startswith("      "):
                skip = False
                out.append(line)
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def patch_config() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    if "environments:" not in text:
        marker = "  # Natural-spawn and border"
        if marker not in text:
            raise SystemExit("could not find insertion point for environments")
        text = text.replace(marker, marker + "\n" + ENVIRONMENTS_YAML.strip().split("\n", 1)[1], 1)

    text = strip_l2_scenarios(text)
    block = build_l2_scenarios_yaml()
    needle = "        boots: IRON_BOOTS\n"
    # Append after the last Level-1 scenario row (ZombieRoom-L1-iron-full-day).
    idx = text.rfind("    ZombieRoom-L1-iron-full-day:")
    if idx == -1:
        raise SystemExit("ZombieRoom-L1-iron-full-day anchor missing")
    boot_idx = text.find(needle, idx)
    if boot_idx == -1:
        raise SystemExit("could not find iron-full-day gear block")
    insert_at = boot_idx + len(needle)
    text = text[:insert_at] + "\n" + block + text[insert_at:]
    CONFIG.write_text(text, encoding="utf-8")
    n = len(ENV_PREFIX) * (len(MOB_VARIANTS) + len(GEAR_VARIANTS))
    print(f"Patched {CONFIG} with Level 2 environments + {n} scenarios")


if __name__ == "__main__":
    patch_config()
