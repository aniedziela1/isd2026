#!/bin/bash
set -euo pipefail

ACTIVE_NODE="osboxes@192.168.115.163"

RUNS=32
FAILOVER_TIME=8
RECOVERY_TIME=12

EVENTS="T5-events.csv"

record_event() {
    local run="$1"
    local event="$2"

    local timestamp_ns
    local timestamp_iso

    timestamp_ns=$(date +%s%N)
    timestamp_iso=$(LC_ALL=C date +"%Y-%m-%dT%H:%M:%S.%N%z")

    echo "$run,$event,$timestamp_ns,$timestamp_iso" >> "$EVENTS"
}

echo "run,event,timestamp_ns,timestamp_iso" > "$EVENTS"

for run in $(seq 1 "$RUNS"); do
    echo
    echo "=== Próba $run/$RUNS ==="

    echo "Wywołanie awarii hp-a..."
    record_event "$run" "STOP_KEEPALIVED"

    ssh "$ACTIVE_NODE" \
        'sudo -n /usr/local/sbin/t5-node-fail'

    echo "Węzeł odłączony. Oczekiwanie ${FAILOVER_TIME}s..."
    sleep "$FAILOVER_TIME"

    echo "Przywracanie hp-a..."
    record_event "$run" "START_KEEPALIVED"

    ssh "$ACTIVE_NODE" \
        'sudo -n /usr/local/sbin/t5-node-restore'

    echo "Węzeł przywrócony. Oczekiwanie ${RECOVERY_TIME}s..."
    sleep "$RECOVERY_TIME"
done

echo
echo "Zakończono. Zdarzenia zapisano w: $EVENTS"
