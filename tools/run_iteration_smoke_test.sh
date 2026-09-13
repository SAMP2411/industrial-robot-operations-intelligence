#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_SEED="${FACTORY_SCENARIO_SEED:-4242}"

# These variables can crash Gazebo's server-side sensor rendering on this machine.
unset LIBGL_ALWAYS_SOFTWARE || true
unset QT_OPENGL || true

set +u
source /opt/ros/jazzy/setup.bash
if [[ -f "$ROOT_DIR/install/setup.bash" ]]; then
  source "$ROOT_DIR/install/setup.bash"
fi
set -u

export FACTORY_SCENARIO_SEED="$DEFAULT_SEED"
export FACTORY_BENCHMARK_SUCCESS_PATTERN="${FACTORY_BENCHMARK_SUCCESS_PATTERN:-Round 1 heading to checkpoint 6/10: mid_east_service_bay}"
export FACTORY_BENCHMARK_TIMEOUT_SECONDS="${FACTORY_BENCHMARK_TIMEOUT_SECONDS:-140}"
LOG_DIR="${FACTORY_BENCHMARK_LOG_DIR:-$HOME/.ros/factory_inspection/benchmark/retry_logs}"

echo "Running iteration smoke test with seed $FACTORY_SCENARIO_SEED"
"$ROOT_DIR/tools/run_benchmark_with_retry.sh" headless:=True use_rviz:=False "$@"
latest_log="$(find "$LOG_DIR" -maxdepth 1 -type f -name 'benchmark_attempt_*.log' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-)"
echo "Smoke test passed. Verified route progress through checkpoint 6/10."
if [[ -n "$latest_log" ]]; then
  echo "Latest smoke-test log: $latest_log"
fi
echo "Latest generated evidence directory: $HOME/.ros/factory_inspection/benchmark"
