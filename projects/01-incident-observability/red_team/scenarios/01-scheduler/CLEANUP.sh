#!/usr/bin/env bash
set -euo pipefail

if [ -f hog.pid ]; then
  pid=$(cat hog.pid)
  echo "[cleanup] killing hog pid=${pid}" >&2
  kill "${pid}" 2>/dev/null || true
  rm -f hog.pid
fi
