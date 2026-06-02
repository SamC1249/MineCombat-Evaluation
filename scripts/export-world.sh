#!/usr/bin/env bash
# Export mcbench_flat from $SERVER into minecombat_eval/data/ and refresh manifest SHA256.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MINECOMBAT_EVAL_ROOT="$ROOT"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi
exec python3 -m minecombat_eval.cli export-world "$@"
