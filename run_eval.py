#!/usr/bin/env python3
"""
Batch eval runner: connect to the plugin TCP port, run episodes, append JSONL rows.

Requires: Paper running with the plugin, one player online (see README).
Run from repo root: python3 run_eval.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, TextIO

from minecombat_eval.agents import AgentFn, make_random_agent, noop_agent
from minecombat_eval.connector import EvaluationConnector, EvaluationProtocolError
from minecombat_eval.loader import load_policy_entry
from minecombat_eval.models import EpisodeResult, PROTOCOL_VERSION

# Failsafe if server never terminates (should match server max-ticks order of magnitude).
_MAX_STEPS = 200_000


def _load_task_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("--task-json must contain a JSON object")
    return obj


def _meta_from_observation(
    obs: dict[str, Any] | None,
) -> tuple[str | None, str | None, str | None, int | None]:
    if not obs:
        return None, None, None, None
    meta = obs.get("meta")
    if not isinstance(meta, dict):
        return None, None, None, None
    pv = meta.get("plugin_version")
    pm = meta.get("paper_minecraft")
    sv = meta.get("scenario_version")
    sl = meta.get("scenario_level")
    ver = str(pv) if pv is not None else None
    pmc = str(pm) if pm is not None else None
    svs = str(sv) if sv is not None else None
    sli: int | None
    try:
        sli = int(sl) if sl is not None else None
    except (TypeError, ValueError):
        sli = None
    return ver, pmc, svs, sli


def run_one_episode(
    conn: EvaluationConnector,
    scenario_id: str,
    seed: int,
    agent_fn: AgentFn,
    *,
    task_spec: dict[str, Any] | None = None,
    suite_id: str | None = None,
    task_id: str | None = None,
    skill_family: str | None = None,
    before_episode: Callable[[dict[str, Any]], None] | None = None,
) -> EpisodeResult:
    ctx: dict[str, Any] = {"scenario_id": scenario_id, "seed": seed}
    if suite_id is not None:
        ctx["suite_id"] = suite_id
    if task_id is not None:
        ctx["task_id"] = task_id
    if skill_family is not None:
        ctx["skill_family"] = skill_family
    if task_spec is not None:
        ctx["task_spec"] = task_spec
    if before_episode is not None:
        before_episode(ctx)
    reset = conn.reset(scenario_id, seed, task_spec=task_spec)
    if reset.get("type") != "reset_ok":
        raise EvaluationProtocolError(
            f"expected reset_ok, got {reset.get('type')!r}",
            raw=reset,
        )
    episode_id = str(reset["episode_id"])
    observation: dict[str, Any] | None = reset.get("observation")  # type: ignore[assignment]
    tick = int(reset.get("tick", 0))

    for _ in range(_MAX_STEPS):
        action = agent_fn(observation, tick)
        sr = conn.step(episode_id, action)
        if sr.get("type") != "step_result":
            raise EvaluationProtocolError(
                f"expected step_result, got {sr.get('type')!r}",
                raw=sr,
            )
        observation = sr.get("observation")  # type: ignore[assignment]
        tick = int(sr.get("tick", tick))
        terminated = bool(sr.get("terminated", False))
        truncated = bool(sr.get("truncated", False))
        if terminated:
            outcome = sr.get("outcome")
            reason = sr.get("reason")
            pv, pm, sver, slvl = _meta_from_observation(
                observation if isinstance(observation, dict) else None
            )
            return EpisodeResult(
                scenario_id=scenario_id,
                seed=int(seed),
                episode_id=episode_id,
                outcome=str(outcome) if outcome is not None else None,
                reason=str(reason) if reason is not None else None,
                ticks=tick,
                truncated=truncated,
                protocol=PROTOCOL_VERSION,
                plugin_version=pv,
                paper_minecraft=pm,
                scenario_version=sver,
                scenario_level=slvl,
                task_spec=task_spec,
                suite_id=suite_id,
                task_id=task_id,
                skill_family=skill_family,
            )

    raise EvaluationProtocolError(
        f"exceeded client step cap ({_MAX_STEPS}); server did not terminate episode"
    )


def _eprint_eval_failure(err: Exception) -> None:
    """One-line diagnostic for common eval wire / server issues (stderr)."""
    s = str(err).lower()
    if "player disconnected" in s:
        print(
            "ERROR: the evaluation player left the Minecraft server during the run; "
            "rejoin, then start a new episode (reset).",
            file=sys.stderr,
        )
    elif "no online player" in s or "join the server" in s:
        print(
            "ERROR: no player is in the world; connect the client, then run again.",
            file=sys.stderr,
        )
    elif isinstance(err, ConnectionError) or "empty read" in s or "closed connection" in s:
        print(
            "ERROR: TCP to the eval server closed (Paper stopped, or connection dropped).",
            file=sys.stderr,
        )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run MineCombat-Evaluation episodes over TCP and log to JSONL."
    )
    p.add_argument(
        "--scenario",
        default="ZombieRoom-v0",
        help="Scenario id (Level 1 registry in plugin config.yml)",
    )
    p.add_argument(
        "--episodes",
        type=int,
        default=1,
        metavar="N",
        help="Number of episodes to run sequentially",
    )
    p.add_argument(
        "--seed-base",
        type=int,
        default=0,
        metavar="K",
        help="Episode i uses seed = seed_base + i (default 0)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="S",
        help="If set, use this seed for every episode (overrides --seed-base)",
    )
    p.add_argument("--host", default="127.0.0.1", help="TCP bind host (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=8765, help="TCP port (default 8765)")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("episodes.jsonl"),
        help="Append one JSON object per finished episode (default: ./episodes.jsonl)",
    )
    p.add_argument(
        "--agent",
        choices=("noop", "random"),
        default="noop",
        help="Stub agent when --policy is not set",
    )
    p.add_argument(
        "--agent-seed",
        type=int,
        default=None,
        metavar="R",
        help="RNG seed for --agent random only",
    )
    p.add_argument(
        "--policy",
        default=None,
        metavar="module:attr",
        help="Custom Policy class or AgentFn (overrides --agent), e.g. minecombat_eval.reference_policy:NoopPolicy",
    )
    p.add_argument(
        "--task-json",
        type=Path,
        default=None,
        metavar="FILE",
        help="Merge JSON task_spec onto --scenario each reset (same fields as docs; optional)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.episodes < 1:
        print("episodes must be >= 1", file=sys.stderr)
        return 2

    before_ep: Callable[[dict[str, Any]], None] | None = None
    if args.policy:
        try:
            agent_fn, before_ep = load_policy_entry(args.policy)
        except (ImportError, ValueError, TypeError) as e:
            print(f"--policy: {e}", file=sys.stderr)
            return 2
    elif args.agent == "random":
        agent_fn = make_random_agent(seed=args.agent_seed)
    else:
        agent_fn = noop_agent

    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    task_spec_obj: dict[str, Any] | None = None
    if args.task_json is not None:
        try:
            task_spec_obj = _load_task_json(args.task_json)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            print(f"--task-json: {e}", file=sys.stderr)
            return 2

    with EvaluationConnector(host=args.host, port=args.port) as conn, out_path.open(
        "a", encoding="utf-8"
    ) as fh:
        return _run_batch(conn, fh, args, agent_fn, before_ep, task_spec_obj)


def _run_batch(
    conn: EvaluationConnector,
    fh: TextIO,
    args: argparse.Namespace,
    agent_fn: AgentFn,
    before_episode: Callable[[dict[str, Any]], None] | None,
    task_spec: dict[str, Any] | None,
) -> int:
    for i in range(args.episodes):
        if args.seed is not None:
            seed = int(args.seed)
        else:
            seed = int(args.seed_base) + i
        try:
            result = run_one_episode(
                conn,
                args.scenario,
                seed,
                agent_fn,
                task_spec=task_spec,
                before_episode=before_episode,
            )
        except (EvaluationProtocolError, OSError, ConnectionError) as e:
            _eprint_eval_failure(e)
            print(f"episode {i + 1}/{args.episodes} failed: {e}", file=sys.stderr)
            return 1
        line = json.dumps(result.to_json_obj(), ensure_ascii=False)
        fh.write(line + "\n")
        fh.flush()
        print(
            f"episode {i + 1}/{args.episodes} seed={seed} "
            f"outcome={result.outcome} reason={result.reason} ticks={result.ticks}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
