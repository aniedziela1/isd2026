#!/bin/bash
set -euo pipefail

DOCKER_HOST="osboxes@192.168.115.162"
CONTAINER="healthcare-1"

RUNS=30
DOWN_TIME=45
RECOVERY_TIME=20

EVENTS="T4-events.csv"

echo "run,event,timestamp_ns,timestamp_iso" > "$EVENTS"

for run in $(seq 1 "$RUNS"); do
    echo "=== Próba $run/$RUNS ==="

    kill_ns=$(date +%s%N)
    kill_iso=$(date --iso-8601=ns)

    echo "$run,KILL,$kill_ns,$kill_iso" >> "$EVENTS"

    ssh "$DOCKER_HOST" \
      "docker kill '$CONTAINER' >/dev/null"

    echo "Kontener zatrzymany. Oczekiwanie ${DOWN_TIME}s..."
    sleep "$DOWN_TIME"

    start_ns=$(date +%s%N)
    start_iso=$(date --iso-8601=ns)

    echo "$run,START,$start_ns,$start_iso" >> "$EVENTS"

    ssh "$DOCKER_HOST" \
      "docker start '$CONTAINER' >/dev/null"

    echo "Kontener uruchomiony. Oczekiwanie ${RECOVERY_TIME}s..."
    sleep "$RECOVERY_TIME"
done

echo "Test zakończony. Zdarzenia zapisano w $EVENTS"
