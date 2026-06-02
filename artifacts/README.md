# Versioned artifacts

Pinned downloads for reproducible bootstrap (`scripts/bootstrap.sh`, `minecombat-eval bootstrap`).

## World: `mcbench_flat-v1`

| Field | Value |
|-------|-------|
| ID | `mcbench_flat-v1` |
| Level name | `mcbench_flat` |
| Zip (shipped in pip) | `minecombat_eval/data/mcbench_flat-v1.zip` |
| SHA256 | `aeef834cb4e80691a5a9f7aac385f156533224cea4f045ad1be5a1e986837ad8` |
| Size | 5 760 423 bytes (~5.5 MB) |

Contains L1 superflat floor (y = −60) and L2 cave/beach builds within the plugin world border.

### Re-export (maintainers)

From a running lab server with the canonical world:

```bash
./scripts/export-world.sh
# or: minecombat-eval export-world
```

Updates zip + `manifest.json` hashes in `minecombat_eval/data/` and `artifacts/`.

## Manifest

`artifacts/manifest.json` mirrors `minecombat_eval/data/manifest.json` (Paper URL, plugin version, suite ids).
