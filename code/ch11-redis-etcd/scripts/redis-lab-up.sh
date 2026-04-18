#!/usr/bin/env bash
# Launch three Redis instances with different appendfsync policies.
# Usage: bash scripts/redis-lab-up.sh
#
# Ports:
#   6379 — appendfsync no
#   6380 — appendfsync everysec
#   6381 — appendfsync always

set -euo pipefail

REDIS_IMAGE="${REDIS_IMAGE:-redis:7}"
BASE_DIR="${1:-$(pwd)/redis-data}"

echo "=== Pulling Redis image ==="
docker pull "$REDIS_IMAGE" 2>/dev/null || true

for policy in no everysec always; do
  case "$policy" in
    no)       port=6379 ;;
    everysec) port=6380 ;;
    always)   port=6381 ;;
  esac

  name="redis-${policy}"
  datadir="${BASE_DIR}/${policy}"
  mkdir -p "$datadir"

  docker rm -f "$name" 2>/dev/null || true

  docker run -d --name "$name" -p "${port}:6379" \
    -v "${datadir}:/data" \
    "$REDIS_IMAGE" \
    redis-server --appendonly yes --appendfsync "$policy"

  echo "  ${name}: port ${port}, appendfsync=${policy}, data=${datadir}"
done

echo ""
echo "=== All Redis instances ==="
docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep redis
echo ""
echo "Test with:"
echo "  redis-cli -p 6379 PING   # no"
echo "  redis-cli -p 6380 PING   # everysec"
echo "  redis-cli -p 6381 PING   # always"
