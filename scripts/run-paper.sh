#!/usr/bin/env bash
# Start Paper with JDK 25 (JAVA_25 from repo .env). Requires SERVER and paper.jar in that folder.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ -z "${JAVA_25:-}" ]]; then
  echo "run-paper.sh: set JAVA_25 in $ROOT/.env to your Temurin 25 Contents/Home path" >&2
  exit 1
fi

: "${SERVER:?Set SERVER in $ROOT/.env (e.g. \$HOME/minecraft-paper-mcbench)}"

export JAVA_HOME="$JAVA_25"
export PATH="$JAVA_HOME/bin:${PATH:-}"

JAR="$SERVER/paper.jar"
if [[ ! -f "$JAR" ]]; then
  echo "run-paper.sh: missing $JAR (copy/download Paper as paper.jar)" >&2
  exit 1
fi

cd "$SERVER"
exec "$JAVA_HOME/bin/java" -Xms2G -Xmx2G -jar paper.jar --nogui
