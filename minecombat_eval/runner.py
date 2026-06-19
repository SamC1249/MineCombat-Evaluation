"""In-process eval/suite runner.

This holds the wire-loop logic that used to live in the repo-root scripts
``run_eval.py`` / ``run_suite.py``. Keeping it in the installed package means the
CLI works from a plain ``pip install minecombat-eval`` with no repo checkout.

The root scripts now import from here, and ``cli.py`` calls ``run_eval`` /
``run_suite`` directly (no subprocess).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .agents import AgentFn, make_random_agent, noop_agent
from .connector import EvaluationConnector, EvaluationProtocolError
from .loader import load_policy_entry
from .models import EpisodeResult, PROTOCOL_VERSION
from .suite import filter_tasks, load_suite, summarize_episode_rows

__all__ = [
    "load_policy_entry",
    "resolve_agent",
    "run_one_episode",
    "eprint_eval_failure",
    "run_eval",
    "run_suite",
]

# Failsafe if the server never terminates an episode (order of magnitude of max-ticks).
_MAX_STEPS = 200_000

BeforeEpisode = Callable[[dict[str, Any]], None]


def _load_task_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
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
    try:
        sli = int(sl) if sl is not None else None
    except (TypeError, ValueError):
        sli = None
    return ver, pmc, svs, sli


def resolve_agent(
    *, policy: str | None, agent: str, agent_seed: int | None
) -> tuple[AgentFn, BeforeEpisode | None]:
    if policy:
        return load_policy_entry(policy)
    if agent == "random":
        return make_random_agent(seed=agent_seed), None
    return noop_agent, None


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
    before_episode: BeforeEpisode | None = None,
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
        raise EvaluationProtocolError(f"expected reset_ok, got {reset.get('type')!r}", raw=reset)
    episode_id = str(reset["episode_id"])
    observation: dict[str, Any] | None = reset.get("observation")
    tick = int(reset.get("tick", 0))

    for _ in range(_MAX_STEPS):
        action = agent_fn(observation, tick)
        sr = conn.step(episode_id, action)
        if sr.get("type") != "step_result":
            raise EvaluationProtocolError(f"expected step_result, got {sr.get('type')!r}", raw=sr)
        observation = sr.get("observation")
        tick = int(sr.get("tick", tick))
        if bool(sr.get("terminated", False)):
            pv, pm, sver, slvl = _meta_from_observation(
                observation if isinstance(observation, dict) else None
            )
            outcome, reason = sr.get("outcome"), sr.get("reason")
            return EpisodeResult(
                scenario_id=scenario_id,
                seed=int(seed),
                episode_id=episode_id,
                outcome=str(outcome) if outcome is not None else None,
                reason=str(reason) if reason is not None else None,
                ticks=tick,
                truncated=bool(sr.get("truncated", False)),
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


def eprint_eval_failure(err: Exception) -> None:
    """One-line diagnostic for common eval wire / server issues (stderr)."""
    s = str(err).lower()
    if "player disconnected" in s:
        print(
            "ERROR: the evaluation player left the Minecraft server during the run; "
            "rejoin, then start a new episode (reset).",
            file=sys.stderr,
        )
    elif "no online player" in s or "join the server" in s:
        print("ERROR: no player is in the world; connect the client, then run again.", file=sys.stderr)
    elif isinstance(err, ConnectionError) or "empty read" in s or "closed connection" in s:
        print("ERROR: TCP to the eval server closed (Paper stopped, or connection dropped).", file=sys.stderr)


def _eprint_connect_failure(err: Exception, host: str, port: int) -> None:
    print(
        f"ERROR: could not connect to the eval server at {host}:{port} ({err}).\n"
        "  Is Paper running? Start it with `minecombat-eval server start`, then join "
        "the world in your Minecraft client before running your agent.",
        file=sys.stderr,
    )


def run_eval(
    *,
    scenario: str = "ZombieRoom-v0",
    episodes: int = 1,
    seed_base: int = 0,
    seed: int | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    output: str | Path = "episodes.jsonl",
    agent: str = "noop",
    agent_seed: int | None = None,
    policy: str | None = None,
    task_json: str | Path | None = None,
) -> int:
    if episodes < 1:
        print("episodes must be >= 1", file=sys.stderr)
        return 2
    try:
        agent_fn, before_ep = resolve_agent(policy=policy, agent=agent, agent_seed=agent_seed)
    except (ImportError, ValueError, TypeError) as e:
        print(f"--policy: {e}", file=sys.stderr)
        return 2
    try:
        task_spec = _load_task_json(Path(task_json) if task_json else None)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"--task-json: {e}", file=sys.stderr)
        return 2

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn_cm = EvaluationConnector(host=host, port=port)
        with conn_cm as conn, out_path.open("a", encoding="utf-8") as fh:
            for i in range(episodes):
                ep_seed = int(seed) if seed is not None else int(seed_base) + i
                try:
                    result = run_one_episode(
                        conn, scenario, ep_seed, agent_fn,
                        task_spec=task_spec, before_episode=before_ep,
                    )
                except (EvaluationProtocolError, OSError, ConnectionError) as e:
                    eprint_eval_failure(e)
                    print(f"episode {i + 1}/{episodes} failed: {e}", file=sys.stderr)
                    return 1
                fh.write(json.dumps(result.to_json_obj(), ensure_ascii=False) + "\n")
                fh.flush()
                print(
                    f"episode {i + 1}/{episodes} seed={ep_seed} "
                    f"outcome={result.outcome} reason={result.reason} ticks={result.ticks}"
                )
    except (OSError, ConnectionError) as e:
        _eprint_connect_failure(e, host, port)
        return 1
    return 0


def run_suite(
    *,
    suite_path: str | Path,
    tasks: str = "",
    tags: str = "",
    episodes: int | None = None,
    seed_base: int | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    output: str | Path = "episodes.jsonl",
    agent: str = "noop",
    agent_seed: int | None = None,
    policy: str | None = None,
    no_summary: bool = False,
) -> int:
    try:
        suite = load_suite(Path(suite_path))
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"--suite: {e}", file=sys.stderr)
        return 2

    task_ids = {t.strip() for t in tasks.split(",") if t.strip()} or None
    tag_set = {t.strip() for t in tags.split(",") if t.strip()} or None
    selected = filter_tasks(suite, task_ids=task_ids, tags=tag_set)
    if not selected:
        print("No tasks matched filters.", file=sys.stderr)
        return 2

    eps = episodes if episodes is not None else suite.episodes_per_task
    base = seed_base if seed_base is not None else suite.seed_base
    if eps < 1:
        print("episodes must be >= 1", file=sys.stderr)
        return 2
    try:
        agent_fn, before_ep = resolve_agent(policy=policy, agent=agent, agent_seed=agent_seed)
    except (ImportError, ValueError, TypeError) as e:
        print(f"--policy: {e}", file=sys.stderr)
        return 2

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    total = len(selected) * eps
    run_idx = 0
    try:
        with EvaluationConnector(host=host, port=port) as conn, out_path.open("a", encoding="utf-8") as fh:
            for task in selected:
                scenario_id = task.scenario_id or suite.default_scenario_id
                for ep in range(eps):
                    run_idx += 1
                    ep_seed = base + ep
                    try:
                        result = run_one_episode(
                            conn, scenario_id, ep_seed, agent_fn,
                            task_spec=task.task_spec, suite_id=suite.suite_id,
                            task_id=task.task_id, skill_family=task.skill_family,
                            before_episode=before_ep,
                        )
                    except (EvaluationProtocolError, OSError, ConnectionError) as e:
                        eprint_eval_failure(e)
                        print(f"run {run_idx}/{total} task={task.task_id} failed: {e}", file=sys.stderr)
                        return 1
                    row = result.to_json_obj()
                    row["suite_version"] = suite.suite_version
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    rows.append(row)
                    print(
                        f"run {run_idx}/{total} task={task.task_id} seed={ep_seed} "
                        f"outcome={result.outcome} reason={result.reason} ticks={result.ticks}"
                    )
    except (OSError, ConnectionError) as e:
        _eprint_connect_failure(e, host, port)
        return 1

    if not no_summary:
        summary = summarize_episode_rows(rows)
        print(
            f"\nSuite {suite.suite_id} v{suite.suite_version}: "
            f"{summary['episodes']} episodes, success_rate={summary['success_rate']:.1%}"
        )
        for tid, stats in sorted(summary["by_task"].items()):
            mt = stats.get("mean_ticks")
            mt_s = f" mean_ticks={mt:.0f}" if isinstance(mt, float) else ""
            print(
                f"  {tid}: {stats['success_rate']:.0%} success "
                f"({stats['successes']}/{stats['episodes']}){mt_s}"
            )
    return 0
