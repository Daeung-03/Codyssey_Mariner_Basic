#!/usr/bin/env bash
set -u

AGENT_HOME="${AGENT_HOME:-/home/agent-admin/agent-app}"
AGENT_PORT="${AGENT_PORT:-15034}"
LOG_DIR="${AGENT_LOG_DIR:-/var/log/agent-app}"
LOG_FILE="${LOG_DIR}/monitor.log"
MAX_LOG_SIZE=$((10 * 1024 * 1024))
MAX_ROTATED_FILES=10

print_header() {
  printf '====== SYSTEM MONITOR RESULT ======\n\n'
}

fail() {
  printf '[FAIL] %s\n' "$1" >&2
  exit 1
}

warn() {
  printf '[WARNING] %s\n' "$1"
}

rotate_log_if_needed() {
  [ -f "$LOG_FILE" ] || return 0

  local size
  size=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
  [ "$size" -lt "$MAX_LOG_SIZE" ] && return 0

  local i
  i=$((MAX_ROTATED_FILES - 1))
  while [ "$i" -ge 1 ]; do
    if [ -f "${LOG_FILE}.${i}" ]; then
      mv "${LOG_FILE}.${i}" "${LOG_FILE}.$((i + 1))"
    fi
    i=$((i - 1))
  done

  mv "$LOG_FILE" "${LOG_FILE}.1"
  : > "$LOG_FILE"
}

find_agent_pid() {
  local candidates=(
    "${AGENT_HOME}/agent-app"
    "agent-app"
    "agent-app-linux"
  )

  local candidate pid stat comm
  for candidate in "${candidates[@]}"; do
    while read -r pid; do
      [ -n "$pid" ] || continue
      stat=$(ps -o stat= -p "$pid" 2>/dev/null || true)
      comm=$(ps -o comm= -p "$pid" 2>/dev/null || true)
      if ! printf '%s\n' "$stat" | grep -q 'Z' &&
        ! printf '%s\n' "$comm" | grep -Eq '^(bash|sh|su|nohup)$'; then
        printf '%s\n' "$pid"
        return 0
      fi
    done < <(pgrep -u agent-admin -f "$candidate" 2>/dev/null || true)
  done

  return 1
}

check_port_listening() {
  ss -tuln | awk -v port=":${AGENT_PORT}" '$1 == "tcp" && $2 == "LISTEN" && index($5, port) { found=1 } END { exit(found ? 0 : 1) }'
}

check_firewall() {
  if command -v ufw >/dev/null 2>&1; then
    if ufw status 2>/dev/null | grep -q '^Status: active'; then
      printf 'Firewall UFW... [OK]\n'
      return 0
    fi
    if [ -r /etc/ufw/ufw.conf ] && grep -q '^ENABLED=yes' /etc/ufw/ufw.conf; then
      printf 'Firewall UFW... [OK]\n'
      return 0
    fi
  fi

  if command -v firewall-cmd >/dev/null 2>&1; then
    if firewall-cmd --state 2>/dev/null | grep -q '^running$'; then
      printf 'Firewall firewalld... [OK]\n'
      return 0
    fi
  fi

  warn 'Firewall is not active'
}

cpu_usage() {
  awk '
    /cpu / {
      idle1=$5
      total1=0
      for (i=2; i<=NF; i++) total1 += $i
    }
    END { printf "%d %d\n", idle1, total1 }
  ' /proc/stat | {
    read -r idle1 total1
    sleep 1
    awk -v idle1="$idle1" -v total1="$total1" '
      /cpu / {
        idle2=$5
        total2=0
        for (i=2; i<=NF; i++) total2 += $i
        total_delta=total2-total1
        idle_delta=idle2-idle1
        if (total_delta <= 0) {
          printf "0.0"
        } else {
          printf "%.1f", (100 * (total_delta - idle_delta) / total_delta)
        }
      }
    ' /proc/stat
  }
}

mem_usage() {
  free | awk '/Mem:/ { printf "%.1f", ($3 / $2) * 100 }'
}

disk_usage() {
  df -P / | awk 'NR == 2 { gsub("%", "", $5); print $5 }'
}

greater_than() {
  awk -v value="$1" -v threshold="$2" 'BEGIN { exit(value > threshold ? 0 : 1) }'
}

main() {
  print_header

  mkdir -p "$LOG_DIR" 2>/dev/null || fail "Cannot create log directory: $LOG_DIR"
  [ -w "$LOG_DIR" ] || fail "Log directory is not writable: $LOG_DIR"
  rotate_log_if_needed

  printf '[HEALTH CHECK]\n'
  printf "Checking process 'agent-app'... "
  local pid
  if ! pid=$(find_agent_pid); then
    printf '[FAIL]\n'
    fail 'Agent app process is not running'
  fi
  printf '[OK] (PID: %s)\n' "$pid"

  printf 'Checking port %s... ' "$AGENT_PORT"
  if ! check_port_listening; then
    printf '[FAIL]\n'
    fail "TCP ${AGENT_PORT} is not LISTEN"
  fi
  printf '[OK]\n'

  check_firewall
  printf '\n'

  local cpu mem disk timestamp
  cpu=$(cpu_usage)
  mem=$(mem_usage)
  disk=$(disk_usage)

  printf '[RESOURCE MONITORING]\n'
  printf 'CPU Usage : %s%%\n' "$cpu"
  printf 'MEM Usage : %s%%\n' "$mem"
  printf 'DISK Used  : %s%%\n\n' "$disk"

  greater_than "$cpu" 20 && warn "CPU threshold exceeded (${cpu}% > 20%)"
  greater_than "$mem" 10 && warn "MEM threshold exceeded (${mem}% > 10%)"
  greater_than "$disk" 80 && warn "DISK threshold exceeded (${disk}% > 80%)"

  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  printf '[%s] PID:%s CPU:%s%% MEM:%s%% DISK_USED:%s%%\n' \
    "$timestamp" "$pid" "$cpu" "$mem" "$disk" >> "$LOG_FILE" \
    || fail "Cannot append log file: $LOG_FILE"

  printf '\n[INFO] Log appended: %s\n' "$LOG_FILE"
}

main "$@"
