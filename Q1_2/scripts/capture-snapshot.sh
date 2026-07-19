#!/usr/bin/env bash

: "${RUN_DIR:?Run 'source scripts/prepare-runtime.sh' first.}"

PID="${1:?Usage: scripts/capture-snapshot.sh <pid> [label]}"
LABEL="${2:-snapshot}"
STAMP=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_DIR="$RUN_DIR/snapshots"
mkdir -p "$SNAPSHOT_DIR"

ps -p "$PID" \
-o pid,ppid,user,stat,pcpu,pmem,rss,nlwp,etime,comm \
> "$SNAPSHOT_DIR/${STAMP}-${LABEL}-process.txt"

ps -eo pid,ppid,user,stat,pcpu,pmem,rss,nlwp,etime,comm --sort=-pcpu \
| head -n 20 \
> "$SNAPSHOT_DIR/${STAMP}-${LABEL}-cpu-ranking.txt"

top -b -n 1 -p "$PID" \
> "$SNAPSHOT_DIR/${STAMP}-${LABEL}-top-process.txt"

top -b -H -n 1 -p "$PID" \
> "$SNAPSHOT_DIR/${STAMP}-${LABEL}-top-threads.txt"

echo "Snapshots saved under: $SNAPSHOT_DIR"