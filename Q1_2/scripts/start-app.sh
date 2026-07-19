#!/usr/bin/env bash

: "${RUN_DIR:?Run 'source scripts/prepare-runtime.sh' first.}"

APP=/workspace/agent-app-leak/agent-leak-app-arm64

if [[ ! -x "$APP" ]]; then
echo "Application is missing or not executable: $APP" >&2
exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

"$APP" > "$RUN_DIR/console.log" 2>&1 &
LAUNCHER_PID=$!
printf '%s\n' "$LAUNCHER_PID" > "$RUN_DIR/launcher.pid"

WORKER_PID=""
for _ in {1..20}; do
WORKER_PID=$(pgrep -P "$LAUNCHER_PID" | head -n 1)

if [[ -n "$WORKER_PID" ]]; then
    break
fi

sleep 0.1
done

if [[ -z "$WORKER_PID" ]]; then
echo "Worker process was not created by launcher PID $LAUNCHER_PID" >&2
exit 1
fi

printf '%s\n' "$WORKER_PID" > "$RUN_DIR/app.pid"

"$SCRIPT_DIR/monitor.sh" "$WORKER_PID" &
MONITOR_PID=$!
printf '%s\n' "$MONITOR_PID" > "$RUN_DIR/monitor.pid"

echo "Started launcher with PID $LAUNCHER_PID"
echo "Started worker with PID $WORKER_PID"
echo "Started monitor with PID $MONITOR_PID"
echo "Console log: $RUN_DIR/console.log"