#!/usr/bin/env bash
set -euo pipefail

# Basic VM-friendly collector (template)
# Captures PSI + vmstat/iostat/pidstat snapshots.

OUT_DIR=${OUT_DIR:-results/collect_$(date +%Y%m%d_%H%M%S)}
DURATION=${DURATION:-30}
PID=${PID:-}    # optional: victim PID

mkdir -p "${OUT_DIR}"

echo "[collect] out=${OUT_DIR} duration=${DURATION}s pid=${PID}" >&2

uname -a > "${OUT_DIR}/uname.txt"
(
  echo "date: $(date -Is)" 
  echo "kernel: $(uname -r)"
) > "${OUT_DIR}/meta.txt"

# PSI
for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
  if [ -f "$f" ]; then
    cat "$f" > "${OUT_DIR}/$(basename $f).txt"
  fi
done

# Periodic samplers (if available)
if command -v vmstat >/dev/null 2>&1; then
  timeout "${DURATION}" vmstat 1 > "${OUT_DIR}/vmstat_1s.txt" &
  echo $! > "${OUT_DIR}/vmstat.pid"
fi

if command -v iostat >/dev/null 2>&1; then
  timeout "${DURATION}" iostat -x 1 > "${OUT_DIR}/iostat_x_1s.txt" &
  echo $! > "${OUT_DIR}/iostat.pid"
fi

if [ -n "${PID}" ] && command -v pidstat >/dev/null 2>&1; then
  timeout "${DURATION}" pidstat -druw -p "${PID}" 1 > "${OUT_DIR}/pidstat_1s.txt" &
  echo $! > "${OUT_DIR}/pidstat.pid"
fi

wait || true

echo "[collect] done" >&2
