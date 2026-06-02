#!/usr/bin/env bash
set -euo pipefail
cd /server
exec java -Xms2G -Xmx2G -jar paper.jar --nogui
