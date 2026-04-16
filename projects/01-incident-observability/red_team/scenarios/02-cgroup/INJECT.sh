#!/usr/bin/env bash
set -euo pipefail

# Template: create a cgroup v2 and apply CPU or memory limits.
# You must adapt this to how you launch your victim workload.
# Recommended in Ubuntu with systemd: systemd-run creates a scoped cgroup.

MODE=${MODE:-cpu}   # cpu|mem

echo "[inject] cgroup boundary mode=${MODE}" >&2

if ! command -v systemd-run >/dev/null 2>&1; then
  echo "[inject] systemd-run not found; please adapt this script for your environment" >&2
  exit 2
fi

echo "[inject] This is a template. Suggested usage:" >&2
cat >&2 <<'EOF'
# CPU quota example:
# sudo systemd-run --scope -p CPUQuota=20% ./your_service
# then run loadgen and observe cpu.stat throttling + p99

# Memory limit example:
# sudo systemd-run --scope -p MemoryMax=512M ./your_service
# then increase working set and observe memory.current + faults/OOM
EOF
