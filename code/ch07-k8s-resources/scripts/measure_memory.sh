#!/bin/bash
# measure_memory.sh - Collect memory metrics
#
# Usage: ./measure_memory.sh <pod-name> <duration-seconds>

POD=${1:-mem-stress}
DURATION=${2:-30}
INTERVAL=1

echo "Collecting memory stats for pod $POD for $DURATION seconds..."
echo "timestamp,memory_current,memory_max,oom_count,oom_kill_count" > memory_data.csv

START_TIME=$(date +%s)
while [ $(($(date +%s) - START_TIME)) -lt $DURATION ]; do
    TIMESTAMP=$(date +%s)
    
    # Get memory stats from pod
    CURRENT=$(kubectl exec $POD -- cat /sys/fs/cgroup/memory.current 2>/dev/null)
    MAX=$(kubectl exec $POD -- cat /sys/fs/cgroup/memory.max 2>/dev/null)
    EVENTS=$(kubectl exec $POD -- cat /sys/fs/cgroup/memory.events 2>/dev/null)
    
    if [ -n "$CURRENT" ]; then
        OOM=$(echo "$EVENTS" | grep "^oom " | awk '{print $2}')
        OOM_KILL=$(echo "$EVENTS" | grep "oom_kill" | awk '{print $2}')
        
        OOM=${OOM:-0}
        OOM_KILL=${OOM_KILL:-0}
        
        # Convert to MB for readability
        CURRENT_MB=$(echo "scale=2; $CURRENT / 1048576" | bc)
        if [ "$MAX" = "max" ]; then
            MAX_MB="unlimited"
        else
            MAX_MB=$(echo "scale=2; $MAX / 1048576" | bc)
        fi
        
        echo "$TIMESTAMP,$CURRENT,$MAX,$OOM,$OOM_KILL" >> memory_data.csv
        echo "[$TIMESTAMP] current=${CURRENT_MB}MB max=${MAX_MB}MB oom=$OOM oom_kill=$OOM_KILL"
    else
        echo "[$TIMESTAMP] Failed to read stats (pod may have been OOMKilled)"
        
        # Check pod status
        STATUS=$(kubectl get pod $POD -o jsonpath='{.status.containerStatuses[0].state}' 2>/dev/null)
        REASON=$(kubectl get pod $POD -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null)
        
        if [ -n "$REASON" ]; then
            echo "           Last termination reason: $REASON"
        fi
    fi
    
    sleep $INTERVAL
done

echo ""
echo "Data saved to memory_data.csv"
