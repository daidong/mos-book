#!/usr/bin/env bash
# Tear down Redis lab instances.

set -euo pipefail

echo "=== Stopping Redis containers ==="
docker stop redis-no redis-everysec redis-always 2>/dev/null || true
docker rm   redis-no redis-everysec redis-always 2>/dev/null || true
echo "Done."
