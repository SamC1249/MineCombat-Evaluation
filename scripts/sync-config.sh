#!/usr/bin/env bash
# Copy repo config template to the live Paper server. Restart Paper after running.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/paper-plugin/src/main/resources/config.yml"

DRY_RUN=0
NO_BACKUP=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--no-backup]

Copies the repo config template to \$SERVER/plugins/MineCombat-Evaluation/config.yml.
Requires SERVER in $ROOT/.env or as an environment variable.

  --dry-run     Print source/dest paths only; do not copy.
  --no-backup   Skip backup of existing dest file.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --no-backup) NO_BACKUP=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${SERVER:?Set SERVER in $ROOT/.env (e.g. \$HOME/minecraft-paper-mcbench)}"

if [[ ! -f "$SRC" ]]; then
  echo "sync-config.sh: missing source $SRC" >&2
  exit 1
fi

DEST_DIR="$SERVER/plugins/MineCombat-Evaluation"
DEST="$DEST_DIR/config.yml"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "SRC=$SRC"
  echo "DEST=$DEST"
  exit 0
fi

if [[ ! -d "$DEST_DIR" ]]; then
  echo "sync-config.sh: destination directory missing: $DEST_DIR" >&2
  echo "Start Paper once with the plugin JAR installed, or create the directory." >&2
  exit 1
fi

if [[ -f "$DEST" && "$NO_BACKUP" -eq 0 ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  cp "$DEST" "$DEST.bak.$STAMP"
  echo "Backed up existing config to $DEST.bak.$STAMP"
fi

cp "$SRC" "$DEST"
echo "Copied config to $DEST"
echo "Restart Paper for changes to take effect."
