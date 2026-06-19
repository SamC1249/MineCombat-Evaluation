#!/usr/bin/env bash
# Refresh wheel-bundled server assets from repo sources before building a release.
# Run after building the plugin (./scripts/run-gradle.sh jar).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/minecombat_eval/data"

JAR_NAME="$(python3 - "$ROOT" <<'PY'
import json, sys
root = sys.argv[1]
print(json.load(open(f"{root}/minecombat_eval/data/manifest.json"))["plugin_jar"])
PY
)"

SRC_JAR="$ROOT/paper-plugin/build/libs/$JAR_NAME"
if [[ ! -f "$SRC_JAR" ]]; then
  echo "sync-package-data: missing built plugin JAR: $SRC_JAR" >&2
  echo "  build it first: ./scripts/run-gradle.sh jar" >&2
  exit 1
fi

mkdir -p "$DATA/plugin" "$DATA/benchmarks"
cp "$SRC_JAR" "$DATA/plugin/$JAR_NAME"
cp "$ROOT/paper-plugin/src/main/resources/config.yml" "$DATA/config.yml"

for suite_dir in "$ROOT"/benchmarks/*/; do
  sid="$(basename "$suite_dir")"
  [[ -f "$suite_dir/suite.json" ]] || continue
  mkdir -p "$DATA/benchmarks/$sid"
  cp "$suite_dir/suite.json" "$DATA/benchmarks/$sid/suite.json"
  if [[ -d "$suite_dir/tasks" ]]; then
    rm -rf "$DATA/benchmarks/$sid/tasks"
    cp -r "$suite_dir/tasks" "$DATA/benchmarks/$sid/tasks"
  fi
done

echo "Synced plugin JAR, config.yml, and suites into $DATA"
