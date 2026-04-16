#!/usr/bin/env bash
set -euo pipefail

if [ -f io.pid ]; then
  pid=$(cat io.pid)
  echo "[cleanup] killing io injector pid=${pid}" >&2
  kill "${pid}" 2>/dev/null || true
  rm -f io.pid
fi
