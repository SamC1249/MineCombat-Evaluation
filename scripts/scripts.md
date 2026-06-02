Concise:

```bash
pip install -e .
minecombat-eval bootstrap
minecombat-eval server start
minecombat-eval run-suite l1-v1 -o results/l1-v1-ref.jsonl
docker compose up --build
```

Also: `./scripts/bootstrap.sh`, `./scripts/export-world.sh`, `./scripts/sync-config.sh`
