#!/usr/bin/env bash

: "${RUN_DIR:?Run 'source scripts/prepare-runtime.sh' first.}"

PID="${1:?Usage: scripts/monitor.sh <pid>}"
INTERVAL=1
MONITOR_LOG="$RUN_DIR/monitor.tsv"
EVENT_LOG="$RUN_DIR/monitor-events.log"

printf 'timestamp\tpid\tstate\tcpu_percent\trss_kb\trss_mb\tthreads\telapsed\tcommand\n' \
> "$MONITOR_LOG"

while true; do
SAMPLE=$(ps -p "$PID" \
    -o pid= -o stat= -o pcpu= -o rss= -o nlwp= -o etime= -o comm=)

if [[ -z "$SAMPLE" ]]; then
    printf '%s\tPID %s is no longer present\n' "$(date -Iseconds)" "$PID" \
    >> "$EVENT_LOG"
    break
fi

read -r OBSERVED_PID STATE CPU RSS_KB THREADS ELAPSED COMMAND <<< "$SAMPLE"
RSS_MB=$(awk -v rss_kb="$RSS_KB" 'BEGIN { printf "%.2f", rss_kb / 1024 }')

printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date -Iseconds)" \
    "$OBSERVED_PID" \
    "$STATE" \
    "$CPU" \
    "$RSS_KB" \
    "$RSS_MB" \
    "$THREADS" \
    "$ELAPSED" \
    "$COMMAND" \
    >> "$MONITOR_LOG"

sleep "$INTERVAL"
done