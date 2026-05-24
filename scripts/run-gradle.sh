#!/usr/bin/env bash
# Run Gradle with JDK 21 (JAVA_21 from repo .env). Example: ./scripts/run-gradle.sh jar
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ -z "${JAVA_21:-}" ]]; then
  echo "run-gradle.sh: set JAVA_21 in $ROOT/.env to your Temurin 21 Contents/Home path" >&2
  exit 1
fi

export JAVA_HOME="$JAVA_21"
export PATH="$JAVA_HOME/bin:${PATH:-}"

cd "$ROOT/paper-plugin"
exec ./gradlew "$@"
