# MVP1 — researcher integration, multi-scenario, optional RL adapter

MVP0 delivers one scenario (`ZombieRoom-v0`), TCP JSON, and batch logging. **MVP1** makes the stack usable for **external policies**, **more than one controlled setup**, and—**optionally**—Gymnasium-style loops for RL users.

Full product vision remains in `planning/initial.md` (Phases 1–2). This doc scopes **MVP1 only**.

---

## Benchmark positioning (what we optimize for)

The **primary research value** is not “Minecraft + combat” in isolation—it is a **reproducible combat-survival evaluation harness**: **versioned protocol**, **registered scenarios**, **episodic outcomes**, and **structured logs** so methods can be compared fairly. Novelty for papers should be framed around **benchmark discipline** (repeatability, explicit terminal reasons, scenario IDs/versions) rather than only “fighting mobs.”

**Default user path:** scripted policies, heuristics, and **LLM-mediated agents** that map observations to actions over TCP—**first-class**, no training loop required.

**Optional path:** online RL or Gym-shaped code for labs that want it; real-time Minecraft remains **slow**, so RL integration is an **adapter**, not the product headline.

---

## Goals

1. **Custom policies** — One documented pattern to plug in researcher code (callable, class-based policy, optional CLI entrypoint) without forking the repo. Prioritize **eval and baselines** over requiring RL infrastructure.
2. **Multiple scenarios / setups** — At least **two** official `scenario_id`s or a **scenario registry** on the Java side so new layouts are data-driven (YAML/JSON + code hooks), not a second copy of `EvaluationEngine` logic.
3. **Reproducibility** — Log and wire fields for **scenario version** / **env fingerprint** when layouts diverge; keep `episodes.jsonl` rows comparable across runs.
4. **RL-shaped environment (optional)** — A small Python **`MineCombatEnv`** (or equivalent) wrapping `EvaluationConnector`: `reset` → `step`, terminal flags, explicit **reward** contract (sparse vs shaped), versioned in docs/protocol when it changes. Ship **after** Policy + registry feel solid so the benchmark story does not depend on Gymnasium.

---

## Non-goals (defer)

- Vectorized parallel envs (N Minecraft servers) as a first-class feature — document **serial** default; parallel = manual N servers + N ports.
- Pip package / PyPI — can follow in a later “usability” milestone (`initial.md` Phase 3).
- Rich observations (pixels, full inventory NBT) — optional later; MVP1 stays close to current JSON observation.
- New player account per episode — assume **one persistent online player** unless explicitly extended.

---

## Architecture (unchanged three layers)

| Layer | MVP1 focus |
|--------|------------|
| **Python public API** | **`Policy` + `run_eval` first**; optional **`MineCombatEnv`** for RL/Gym users. |
| **Evaluation / control** | Still the plugin TCP server + episode loop; reward may remain 0 until defined in protocol. |
| **Paper backend** | Scenario registry: `scenario_id` → spawn rules, bounds, gear, terminal conditions, max ticks. |

---

## 1. Policies (researcher-facing)

**Minimal contract**

- **Input:** `observation` (dict, protocol-defined) + `tick` + optional `info` (episode id, scenario id).
- **Output:** `Action` (same fields as wire; already in `minecombat_eval.models`).

**Supported patterns**

- **Callable** — Same as today’s `AgentFn`; good for scripts and baselines.
- **Class `Policy`** — `reset(ctx)` optional + `act(obs, tick)` for recurrent or stateful agents.
- **Entry point** — e.g. `module.path:callable` or small YAML for paper-style reproducibility.

**Deliverables**

- `planning/agent-integration.md` (or README section): lead with **eval / heuristic / LLM** usage; minimal example + one **reference policy** (rule-based or tiny model on a flat vector if you add `ObsEncoder`).

---

## 2. Benchmark vs RL (optional adapter)

**Three modes** (document all three; **MVP1 priority = mode 1**):

1. **Eval-only (default story)** — Policies map obs → action over TCP; aggregate metrics from `episodes.jsonl`. Training happens off-env if at all. Matches most LLM-agent and heuristic work.
2. **Online RL** — `MineCombatEnv` + Gymnasium `reset` / `step` when users opt in; reward from plugin or client-side stub until protocol defines `reward` semantics.
3. **Offline / logs** — Consume `episodes.jsonl` (+ optional future tick traces).

**Reward**

- Prefer **sparse terminal** for benchmark comparability; add **optional shaping** only behind a named mode so papers state which reward they used.

**Dependencies**

- Core path stays **stdlib**; optional **`gymnasium`** extra for users who want `Env` registration—clearly labeled optional in README.

---

## 3. Environments and scenarios

**Minimal multi-setup model**

- **`scenario_id`** in `reset` selects a **registered scenario** on the server.
- Each scenario specifies: world name (default shared), arena bounds, player/zombie (or mob list) spawns, gear, `max-ticks`, success/fail rules.
- **Same world, different coords/recipes** covers most MVP1 needs; optional second `level-name` per scenario if required.

**Versioning**

- Include **`scenario_version`** (or hash) in logs and optionally in `reset`/`reset_ok` once multiple layouts exist.

**Departure from “one mod respawn”**

- Waves, multiple mob types, or phased spawns = **one scenario** with internal state machine in the plugin, still one episode per `reset` unless protocol adds sub-episodes later.

---

## 4. Protocol and docs

- Extend **`planning/protocol-v1.md`** (or v2) for: optional `reward`, `scenario_version`, any new terminal reasons.
- **README**: benchmark-first one-liner; short **Eval vs train** subsection pointing to `agent-integration` and `mvp1.md` (heuristic/LLM before RL).

---

## 5. Suggested implementation order

1. **Java:** scenario registry + second official scenario (proves non-single-hardcoded path).
2. **Python:** `Policy` ABC + refactor `run_one_episode` / `run_eval.py` to accept `Policy` and optional `--policy` entrypoint.
3. **Docs:** agent integration guide (eval/heuristic/LLM first) + README pointers; update `tasks.md` checkboxes.
4. **Python (optional):** `MineCombatEnv` + Gymnasium soft extra—after the above so RL is clearly layered on top of the benchmark.

---

## References

- `planning/initial.md` — long-range roadmap and scenario families.
- `planning/protocol-v1.md` — wire schema.
- `planning/tasks.md` — MVP1 checklist.
