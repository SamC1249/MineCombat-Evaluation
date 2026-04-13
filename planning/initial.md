Here’s a 3-page-style plan you can use as a working blueprint.

# Plan for a Minecraft Java Combat Evaluation Package and Benchmark Suite

## 1. Goal and product definition

The package should make it easy for researchers to evaluate embodied agents in Minecraft Java on a narrow, repeatable question:

**Can the agent kill hostile mobs and survive under controlled conditions?**

The main design principle is that this should feel like a standard research benchmark package, not like a custom server hack. A user should be able to install the package, choose a scenario, connect an agent, run episodes, and get structured results without needing to understand Minecraft internals.

The package should serve two audiences at once. The first is the **benchmark user**, who wants to run evaluations quickly. The second is the **benchmark developer**, who wants to add new scenarios, metrics, and backends over time. To support both, the system should separate the public API from the Minecraft-specific machinery underneath.

The project should aim for four concrete outcomes in version 1:

1. A small Python package with a clean environment interface.
2. A Java-side benchmark backend that can reset arenas, spawn mobs, and collect results.
3. A scenario format that allows new evaluations to be added without code changes.
4. A reporting pipeline that outputs per-episode logs and aggregate benchmark summaries.

The package should not try to solve every embodied task in Minecraft. It should stay tightly scoped around **combat-survival evaluation**, because that is what makes the benchmark interpretable and easy to reproduce.

---

## 2. High-level architecture

The cleanest architecture is a **three-layer system**.

### Layer 1: Public package interface

This is the part users import. It should expose a Gym-style or MineRL-style environment API:

```python
env = mcbench.make("ZombieRoom-v1")
obs, info = env.reset(seed=42)

done = False
while not done:
    action = agent.act(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
```

This layer should feel familiar to RL researchers, LLM agent researchers, and general embodied-agent users. It should hide the complexity of Minecraft orchestration.

### Layer 2: Evaluation service

This is the control layer that manages episodes. It should:

* load scenarios
* reset world state
* initialize the agent
* start and stop trials
* track metrics
* save logs
* return observations and outcomes to the Python package

This layer is the real heart of the benchmark.

### Layer 3: Minecraft backend

This is the Java-side implementation that actually runs the world. For your use case, this should likely be a Paper-based backend in v1 because it gives you direct control over spawning, world state, and event logging. Internally, this layer should expose only a narrow control surface to the evaluation service: reset, spawn, observe, apply action, and terminate.

This architecture gives you flexibility. If later you want a MineRL-compatible backend, a Fabric backend, or a different simulator layer, you can add that without changing the benchmark API.

---

## 3. Core package components

The package should be organized into six core modules.

### A. Environment API

This module exposes the Python-facing interface. It should handle:

* environment creation
* reset and step
* action validation
* episode termination
* scenario selection
* optional seeding

This is what outside users interact with most, so it should be as small and stable as possible.

### B. Scenario registry

This module should load scenario definitions from structured files. Each scenario should specify:

* arena or map template
* starting position
* mob types, counts, and spawn rules
* player gear and initial state
* time limit
* success and failure conditions
* metrics to record

A typical scenario should be declarative, not hardcoded. That makes the suite easier to extend and easier to publish as a benchmark.

### C. Backend connector

This module should manage communication between the Python package and the Minecraft backend. It should define a simple protocol for:

* reset requests
* state observations
* action submission
* event messages
* final episode summaries

You do not need an elaborate protocol in v1. JSON messages over a local socket or WebSocket are enough, as long as the schema is explicit and versioned.

### D. Metrics engine

This module computes benchmark outputs. It should track:

* success or failure
* survival
* mobs killed
* damage taken
* time to clear
* time survived
* remaining health
* resources consumed

The metrics engine should also produce aggregate outputs like:

* success rate by scenario
* survival rate by scenario
* average time to clear
* average damage taken
* confidence intervals across repeated runs

### E. Logging and replay

This module should save both summary results and detailed traces. A good structure is:

* `episodes.jsonl` for one summary row per run
* `events.jsonl` for detailed event streams
* optional tick-level traces for debugging harder failures

This module becomes extremely important when a user asks, “Why did my agent fail on this scenario?”

### F. Evaluation runner

This module should support benchmark execution across many runs. It should allow a user to say:

* run one scenario 100 times
* run all scenarios in a suite
* compare two agents on the same scenario set
* export a report

This is the main entry point for benchmark experiments.

---

## 4. Benchmark design and scenario philosophy

The evaluation suite should be built around **scenario families**, not one giant score. This is how you keep results meaningful.

A useful scenario set for v1 would include:

### Family 1: Basic mob handling

These are simple one-threat tests:

* single zombie in open arena
* single skeleton at fixed range
* single spider in enclosed space
* single creeper with enough room to kite

These establish whether the agent understands basic combat against individual mobs.

### Family 2: Mixed combat

These combine threat types:

* zombie plus skeleton
* two zombies plus one skeleton
* spider plus zombie
* creeper mixed into melee pressure

These test target selection and threat prioritization.

### Family 3: Pressure and endurance

These focus on survival under sustained stress:

* sequential waves
* no healing between waves
* low starting health
* short cooldown between spawn phases

These evaluate stability and robustness rather than only one-fight competence.

### Family 4: Generalization variants

These change the context while keeping the task recognizable:

* larger or smaller rooms
* limited cover
* random spawn angles
* different starting equipment
* randomized but bounded mob counts

These are important because otherwise agents may overfit to exact layouts.

For every scenario, define explicit terminal conditions. Good examples:

* all hostile mobs dead and agent alive
* agent survives for 60 seconds
* agent kills at least N mobs before timeout
* agent dies
* timeout reached

This makes the benchmark easy to reason about and easy to report in papers or internal experiments.

---

## 5. Observation and action interface

To make the package easy for others to adopt, the agent interface should be minimal and well documented.

### Observation design

The observation should contain only the information needed for the task, plus a few diagnostics. A strong v1 observation might include:

* tick number
* health and hunger
* position and orientation
* held item and hotbar state
* nearby hostile mobs with type, relative position, approximate health if available, and line-of-sight flag
* nearby blocks or simple terrain affordances
* active effects
* last damage received
* whether the agent is on the ground

You can later add raw pixels or richer observations, but the base schema should stay simple. The most important thing is to version it. If the observation structure changes, benchmark comparisons should not silently mix old and new setups.

### Action design

The action schema should also be narrow:

* movement inputs
* yaw and pitch changes
* jump
* attack
* use
* crouch or sprint
* hotbar selection

This is enough for combat-survival evaluation. Avoid adding complex crafting or high-level planning APIs to the initial version, because they will make adoption harder and evaluation noisier.

---

## 6. Development roadmap

The package should be built in four phases.

### Phase 1: Minimal viable benchmark

Goal: produce one working end-to-end evaluation.

Deliverables:

* Paper backend that can load a small arena
* one Python environment wrapper
* two scenarios
* success/failure logging
* batch execution across repeated seeds

At the end of this phase, a user should be able to run:
`python run_eval.py --scenario ZombieRoom-v1 --episodes 50`

### Phase 2: Scenario and metric expansion

Goal: make the suite useful beyond demos.

Deliverables:

* 8 to 12 scenarios across several mob types
* richer metrics
* structured reports
* scenario registry
* consistent seeding and version stamping

At the end of this phase, the suite should already be publishable as an internal benchmark.

### Phase 3: Usability and packaging

Goal: make outside adoption realistic.

Deliverables:

* pip-installable Python package
* CLI entry points
* setup guide
* reference agent examples
* benchmark cards documenting each scenario
* reproducibility instructions

At this phase, ease of use matters more than adding more scenarios.

### Phase 4: Research-grade improvements

Goal: support broader external use.

Deliverables:

* MineRL-style compatibility layer if needed
* optional richer observation modes
* comparison reports across multiple agents
* held-out scenario split for generalization testing
* benchmark leaderboard format

This phase is where you turn a useful tool into a credible community benchmark.

---

## 7. Packaging and distribution strategy

The benchmark should be distributed like a normal research tool, not like a one-off game mod.

The recommended distribution model is:

* a Python package as the main entry point
* a bundled or separately versioned Java backend artifact
* scenario files shipped with the package
* a small CLI for running evaluations and generating reports

A user experience target should be:

1. install package
2. launch backend
3. run a benchmark
4. inspect JSON or CSV results

To support reproducibility, every run should stamp:

* package version
* scenario version
* backend version
* Minecraft version
* agent name and version
* seed

This becomes essential once the suite is used for model comparisons.

---

## 8. Documentation plan

Good documentation will decide whether others actually use the package.

You should write four pieces of documentation first:

### Quickstart

Shows how to install, run one benchmark, and read the output.

### Agent integration guide

Shows how to implement a minimal agent class and connect it to the environment.

### Scenario authoring guide

Explains how to create a new evaluation by writing a scenario file.

### Benchmark reference

Lists all official scenarios, what they measure, and what counts as success.

The documentation should emphasize that users do not need to understand Minecraft internals to run the suite.

---

## 9. Risks and mitigation

The biggest risk is trying to build too much too early. If you attempt open-world tasks, dense observations, many backends, and a large task set in v1, the project will become hard to stabilize.

A second risk is overfitting the suite to one agent architecture. The fix is to keep the observation-action API generic and the benchmark logic externalized in scenarios.

A third risk is hidden non-determinism. Minecraft can be noisy, so you should control arenas, seeds, rules, and reset logic carefully from the beginning.

A fourth risk is poor usability. If outside users have to patch Minecraft internals or hand-edit many config files, they will not adopt the suite. The cure is a narrow API, example agents, and one-command evaluation runs.

---

## 10. Recommended v1 definition of success

Version 1 should be considered successful if it can do the following reliably:

* run at least 5 to 10 official combat-survival scenarios
* support repeated evaluation over many episodes
* expose a simple Python API
* accept actions from an external agent
* generate reproducible summary metrics
* produce enough logs to diagnose failures
* allow new scenarios to be added from data files

That is enough to make the benchmark genuinely useful.

The key strategic decision is this:

**Build the benchmark core around controlled scenario execution and logging, then expose it through a simple Python environment interface.**

That gives you a package that is both technically solid and easy for others to use.

If you want, I can turn this into a more formal design doc with sections like objectives, non-goals, architecture, milestones, and repo layout.
