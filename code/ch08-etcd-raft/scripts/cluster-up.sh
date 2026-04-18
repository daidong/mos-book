#!/usr/bin/env bash
# Start a 3-node etcd cluster in Docker containers.
# Usage: bash scripts/cluster-up.sh
#
# Prerequisites:
#   docker pull quay.io/coreos/etcd:v3.5.17
#   (or set ETCD_IMAGE to another tag)

set -euo pipefail

ETCD_IMAGE="${ETCD_IMAGE:-quay.io/coreos/etcd:v3.5.17}"
NETWORK="etcd-net"
TOKEN="lab8-cluster"

echo "=== Creating Docker network ==="
docker network create "$NETWORK" 2>/dev/null || true

echo "=== Starting 3 etcd nodes ==="
for i in 1 2 3; do
  port_client=$((2379 + (i-1)*2))
  name="etcd${i}"
  node="node${i}"

  docker rm -f "$name" 2>/dev/null || true

  docker run -d --name "$name" --network "$NETWORK" \
    -p "${port_client}:2379" \
    "$ETCD_IMAGE" etcd \
    --name "$node" \
    --initial-advertise-peer-urls "http://${name}:2380" \
    --listen-peer-urls http://0.0.0.0:2380 \
    --advertise-client-urls "http://${name}:2379" \
    --listen-client-urls http://0.0.0.0:2379 \
    --initial-cluster "node1=http://etcd1:2380,node2=http://etcd2:2380,node3=http://etcd3:2380" \
    --initial-cluster-state new \
    --initial-cluster-token "$TOKEN"

  echo "  ${name}: client port ${port_client}"
done

sleep 3
echo ""
echo "=== Cluster health ==="
docker exec -e ETCDCTL_API=3 etcd1 etcdctl \
  --endpoints=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379 \
  endpoint health

echo ""
echo "=== Cluster status ==="
docker exec -e ETCDCTL_API=3 etcd1 etcdctl \
  --endpoints=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379 \
  endpoint status -w table

echo ""
echo "Helper aliases (paste into your shell):"
echo '  etcdctl_in() { docker exec -e ETCDCTL_API=3 "$1" etcdctl "${@:2}"; }'
echo '  export CLUSTER_EP=http://etcd1:2379,http://etcd2:2379,http://etcd3:2379'
echo '  export HOST_CLUSTER_EP=http://127.0.0.1:2379,http://127.0.0.1:2381,http://127.0.0.1:2382'
