#!/usr/bin/env bash
set -euo pipefail

# Template injection: create CPU contention on a chosen core.
# Adapt this to your workload (pin hog to the same CPU as the service).

CPU=${CPU:-0}
THREADS=${THREADS:-4}
DURATION=${DURATION:-30}

echo "[inject] scheduler/noisy-neighbor: cpu=${CPU} threads=${THREADS} duration=${DURATION}s" >&2

if command -v stress-ng >/dev/null 2>&1; then
  # --taskset pins workers to CPU
  stress-ng --cpu "${THREADS}" --taskset "${CPU}" --timeout "${DURATION}s" &
  echo $! > hog.pid
  echo "[inject] stress-ng pid=$(cat hog.pid)" >&2
else
  echo "[inject] stress-ng not found; install with: sudo apt-get install -y stress-ng" >&2
  echo "[inject] fallback: starting a simple busy loop (un-pinned)" >&2
  (end=$((SECONDS + DURATION)); while [ $SECONDS -lt $end ]; do :; done) &
  echo $! > hog.pid
fi
