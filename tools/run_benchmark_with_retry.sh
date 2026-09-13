#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ATTEMPTS="${FACTORY_BENCHMARK_MAX_ATTEMPTS:-3}"
TIMEOUT_SECONDS="${FACTORY_BENCHMARK_TIMEOUT_SECONDS:-160}"
POLL_SECONDS="${FACTORY_BENCHMARK_POLL_SECONDS:-2}"
SUCCESS_PATTERN="${FACTORY_BENCHMARK_SUCCESS_PATTERN:-Round 1 summary:}"
LOG_DIR="${FACTORY_BENCHMARK_LOG_DIR:-$HOME/.ros/factory_inspection/benchmark/retry_logs}"
mkdir -p "$LOG_DIR"

# These variables can crash Gazebo's server-side sensor rendering on this machine.
unset LIBGL_ALWAYS_SOFTWARE || true
unset QT_OPENGL || true

set +u
source /opt/ros/jazzy/setup.bash
if [[ -f "$ROOT_DIR/install/setup.bash" ]]; then
  source "$ROOT_DIR/install/setup.bash"
fi
set -u

last_log=""

for attempt in $(seq 1 "$ATTEMPTS"); do
  "$ROOT_DIR/tools/clean_benchmark_runtime.sh"
  timestamp="$(date +%Y%m%d_%H%M%S)"
  log_path="$LOG_DIR/benchmark_attempt_${timestamp}_${attempt}.log"
  last_log="$log_path"
  echo "Benchmark attempt $attempt/$ATTEMPTS starting. Log: $log_path"

  (
    cd "$ROOT_DIR"
    ros2 launch factory_inspection_mission benchmark_patrol.launch.py "$@" \
      >"$log_path" 2>&1
  ) &
  launch_pid=$!
  deadline=$((SECONDS + TIMEOUT_SECONDS))
  success=false
  failure_reason=""

  while kill -0 "$launch_pid" 2>/dev/null; do
    if grep -q "$SUCCESS_PATTERN" "$log_path" 2>/dev/null; then
      success=true
      break
    fi

    if grep -q "Unable to find or download file" "$log_path" 2>/dev/null; then
      failure_reason="gazebo_asset_startup_flake"
      break
    fi

    if grep -q "process has died.*gz" "$log_path" 2>/dev/null; then
      failure_reason="gazebo_process_died"
      break
    fi

    if grep -q "Failed to bring up all requested nodes. Aborting bringup." "$log_path" 2>/dev/null; then
      failure_reason="nav2_bringup_failed"
      break
    fi

    if grep -q "Mission placed in HOLD" "$log_path" 2>/dev/null; then
      failure_reason="mission_hold"
      break
    fi

    if grep -Eq "Round [0-9]+ summary:.*status=FAILURE" "$log_path" 2>/dev/null; then
      failure_reason="mission_round_failed"
      break
    fi

    if (( SECONDS >= deadline )); then
      failure_reason="timeout_waiting_for_success_pattern"
      break
    fi

    sleep "$POLL_SECONDS"
  done

  if [[ "$success" == true ]]; then
    echo "Benchmark succeeded on attempt $attempt. Log: $log_path"
    kill -INT "$launch_pid" 2>/dev/null || true
    sleep 2
    kill -TERM "$launch_pid" 2>/dev/null || true
    wait "$launch_pid" 2>/dev/null || true
    "$ROOT_DIR/tools/clean_benchmark_runtime.sh"
    exit 0
  fi

  kill -TERM "$launch_pid" 2>/dev/null || true
  sleep 2
  kill -KILL "$launch_pid" 2>/dev/null || true
  wait "$launch_pid" 2>/dev/null || true
  "$ROOT_DIR/tools/clean_benchmark_runtime.sh"

  echo "Benchmark attempt $attempt/$ATTEMPTS failed: ${failure_reason:-launch_exited_without_success}. Log: $log_path"
done

echo "Benchmark failed after $ATTEMPTS attempts. Last log: $last_log"
exit 1
