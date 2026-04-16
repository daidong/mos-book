#!/usr/bin/env bash
set -euo pipefail

echo "[cleanup] If you used systemd-run --scope, stop the scope/unit you created." >&2
echo "[cleanup] Example: sudo systemctl stop run-XYZ.scope" >&2
