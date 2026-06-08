# Custom policy examples

Three runnable policies showing the patterns most researchers use. Full guide:
[`docs/policy-porting.md`](../../docs/policy-porting.md).

| File | Kind | When to use |
|------|------|-------------|
| [`scripted_policy.py`](scripted_policy.py) | scripted | Fixed action sequence; smoke-test the loop |
| [`conditional_policy.py`](conditional_policy.py) | conditional | Hand-written heuristic (target/aim/attack) |
| [`torch_policy.py`](torch_policy.py) | torch | Wrap a trained `.pt` model |

## Validate offline (no Minecraft)

From the repo root:

```bash
minecombat-eval test-policy examples.custom_policy.scripted_policy:ScriptedPolicy
minecombat-eval test-policy examples.custom_policy.conditional_policy:ConditionalPolicy
```

`test-policy` imports the policy, runs `act()` on synthetic observations of a mob
approaching the player, and checks every returned `Action` for valid shape and
ranges. It catches import errors, exceptions, and bad outputs before you spend
time on a live server.

## Run against a live server

With Paper + the plugin running and one player online (see the repo README):

```bash
minecombat-eval run-eval  --policy examples.custom_policy.conditional_policy:ConditionalPolicy
minecombat-eval run-suite l1-v1 --policy examples.custom_policy.conditional_policy:ConditionalPolicy -o results/l1.jsonl
```

## Start your own

```bash
minecombat-eval init-policy my_agent --kind conditional
```

This scaffolds an importable `my_agent/` package you can edit, then test with
`minecombat-eval test-policy my_agent.policy:MyAgentPolicy`.
