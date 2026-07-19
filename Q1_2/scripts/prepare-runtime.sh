#!/usr/bin/env bash
# This file is sourced by an interactive shell, so it must not change shell error options.

: "${CASE_NAME:=manual}"
: "${RUN_ID:=$(date +%Y%m%d-%H%M%S)}"
: "${MEMORY_LIMIT:=50}"
: "${CPU_MAX_OCCUPY:=50}"
: "${MULTI_THREAD_ENABLE:=true}"

export CASE_NAME RUN_ID MEMORY_LIMIT CPU_MAX_OCCUPY MULTI_THREAD_ENABLE

export AGENT_HOME=/workspace/runtime
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys"
export RUN_DIR="/workspace/artifacts/$CASE_NAME/$RUN_ID"
export AGENT_LOG_DIR="$RUN_DIR/app-logs"

mkdir -p "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
printf '%s\n' 'agent_api_key_test' > "$AGENT_KEY_PATH/secret.key"

echo "CASE_NAME=$CASE_NAME"
echo "RUN_ID=$RUN_ID"
echo "RUN_DIR=$RUN_DIR"
echo "MEMORY_LIMIT=$MEMORY_LIMIT MB"
echo "CPU_MAX_OCCUPY=$CPU_MAX_OCCUPY%"