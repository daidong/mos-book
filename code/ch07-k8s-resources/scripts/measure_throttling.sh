#!/bin/bash
# measure_throttling.sh - Collect CPU throttling metrics
#
# Usage: ./measure_throttling.sh <pod-name> <duration-seconds>

POD=${1:-cpu-stress}
DURATION=${2:-30}
INTERVAL=1

echo "Collecting CPU stats for pod $POD for $DURATION seconds..."
echo "timestamp,nr_periods,nr_throttled,throttled_usec" > cpu_throttle_data.csv

START_TIME=$(date +%s)
while [ $(($(date +%s) - START_TIME)) -lt $DURATION ]; do
    TIMESTAMP=$(date +%s)
    
    # Get cpu.stat from pod
    STATS=$(kubectl exec $POD -- cat /sys/fs/cgroup/cpu.stat 2>/dev/null)
    
    if [ -n "$STATS" ]; then
        NR_PERIODS=$(echo "$STATS" | grep "nr_periods" | awk '{print $2}')
        NR_THROTTLED=$(echo "$STATS" | grep "nr_throttled" | awk '{print $2}')
        THROTTLED_USEC=$(echo "$STATS" | grep "throttled_usec" | awk '{print $2}')
        
        echo "$TIMESTAMP,$NR_PERIODS,$NR_THROTTLED,$THROTTLED_USEC" >> cpu_throttle_data.csv
        echo "[$TIMESTAMP] periods=$NR_PERIODS throttled=$NR_THROTTLED usec=$THROTTLED_USEC"
    else
        echo "[$TIMESTAMP] Failed to read stats"
    fi
    
    sleep $INTERVAL
done

echo ""
echo "Data saved to cpu_throttle_data.csv"
echo ""

# Calculate summary
if [ -f cpu_throttle_data.csv ]; then
    FIRST=$(tail -n +2 cpu_throttle_data.csv | head -1)
    LAST=$(tail -1 cpu_throttle_data.csv)
    
    FIRST_PERIODS=$(echo $FIRST | cut -d',' -f2)
    LAST_PERIODS=$(echo $LAST | cut -d',' -f2)
    FIRST_THROTTLED=$(echo $FIRST | cut -d',' -f3)
    LAST_THROTTLED=$(echo $LAST | cut -d',' -f3)
    
    DELTA_PERIODS=$((LAST_PERIODS - FIRST_PERIODS))
    DELTA_THROTTLED=$((LAST_THROTTLED - FIRST_THROTTLED))
    
    if [ $DELTA_PERIODS -gt 0 ]; then
        RATIO=$(echo "scale=2; $DELTA_THROTTLED * 100 / $DELTA_PERIODS" | bc)
        echo "Summary:"
        echo "  Total periods: $DELTA_PERIODS"
        echo "  Throttled periods: $DELTA_THROTTLED"
        echo "  Throttle ratio: ${RATIO}%"
    fi
fi
