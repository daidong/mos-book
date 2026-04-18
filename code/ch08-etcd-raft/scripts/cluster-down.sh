#!/usr/bin/env bash
# Tear down the 3-node etcd cluster and the single-node instance.
# Usage: bash scripts/cluster-down.sh

set -euo pipefail

echo "=== Stopping etcd containers ==="
docker stop etcd1 etcd2 etcd3 etcd-single 2>/dev/null || true
docker rm   etcd1 etcd2 etcd3 etcd-single 2>/dev/null || true

echo "=== Removing network ==="
docker network rm etcd-net 2>/dev/null || true

echo "Done."
