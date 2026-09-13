#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROS_SETUP="/opt/ros/jazzy/setup.bash"
RUNTIME_ROOT_DEFAULT="$HOME/.ros/factory_inspection/benchmark"
QUEUE_PATH_DEFAULT="$HOME/.ros/factory_inspection/operator/operator_mission_queue.yaml"
STACK_RUNTIME_DIR="$HOME/.ros/factory_inspection/live_demo_stack"
RUNNER_DIR="$STACK_RUNTIME_DIR/runners"

HEADLESS="False"
USE_RVIZ="True"
ROBOT_PROFILE="tb4"
ROBOT_NAME="scout_alpha"
SCENARIO_SEED="${FACTORY_SCENARIO_SEED:-4242}"
FLEETWATCH_PORT="${FLEETWATCH_PORT:-8000}"
RUN_BUILD=true
OPEN_BROWSER=true
RUN_FLEETWATCH=true
RUN_WATCHERS=true
DRY_RUN=false
TERMINAL_APP=""

log() {
  printf '[live-demo] %s\n' "$*"
}

die() {
  printf '[live-demo] ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./tools/run_live_demo_stack.sh [options]

Launches the live robotics demo stack:
- Gazebo + robot + Nav2 + mission control
- FleetWatch operator console
- patrol summary watcher
- artifact / queue watcher

Options:
  --headless              Run Gazebo server without GUI.
  --no-rviz               Do not launch RViz.
  --skip-build            Skip colcon build before launch.
  --skip-fleetwatch       Do not start the FleetWatch API/UI.
  --skip-watchers         Do not start watcher terminals.
  --no-browser            Do not auto-open FleetWatch or dashboard pages.
  --robot-profile NAME    Robot profile to launch. Default: tb4
  --robot-name NAME       Robot name to launch. Default: scout_alpha
  --seed VALUE            Scenario seed. Default: 4242
  --fleetwatch-port PORT  FleetWatch port. Default: 8000
  --terminal APP          Terminal app to use. Supported: gnome-terminal, xterm
  --dry-run               Print the generated commands without launching them.
  --help                  Show this help.
EOF
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

pick_terminal() {
  if [[ -n "$TERMINAL_APP" ]]; then
    command -v "$TERMINAL_APP" >/dev/null 2>&1 || die "Requested terminal app not found: $TERMINAL_APP"
    return
  fi

  if command -v gnome-terminal >/dev/null 2>&1; then
    TERMINAL_APP="gnome-terminal"
    return
  fi
  if command -v xterm >/dev/null 2>&1; then
    TERMINAL_APP="xterm"
    return
  fi

  die "Neither gnome-terminal nor xterm is installed."
}

load_fleetwatch_env() {
  if [[ -f "$ROOT_DIR/fleet_api/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/fleet_api/.env"
    set +a
  fi

  export FLEETWATCH_SQLITE_PATH="${FLEETWATCH_SQLITE_PATH:-$ROOT_DIR/fleet_api/data/fleetwatch.db}"
  export FACTORY_BENCHMARK_RUNTIME_ROOT="${FACTORY_BENCHMARK_RUNTIME_ROOT:-$RUNTIME_ROOT_DEFAULT}"
  export FACTORY_OPERATOR_QUEUE_PATH="${FACTORY_OPERATOR_QUEUE_PATH:-$QUEUE_PATH_DEFAULT}"
  export FACTORY_SITE_CONFIG="${FACTORY_SITE_CONFIG:-$ROOT_DIR/src/factory_inspection_mission/config/sites/benchmark_site.yaml}"
  export FACTORY_ASSET_REGISTRY="${FACTORY_ASSET_REGISTRY:-$ROOT_DIR/src/factory_inspection_mission/config/assets/benchmark_asset_registry.yaml}"
  export FACTORY_INSPECTION_PROFILES="${FACTORY_INSPECTION_PROFILES:-$ROOT_DIR/src/factory_inspection_mission/config/inspection_profiles/benchmark_inspection_profiles.yaml}"
  export SECRET_KEY="${SECRET_KEY:-local-fleetwatch-demo-secret}"
  export DEMO_EMAIL="${DEMO_EMAIL:-sam@fleetwatch.io}"
  export DEMO_PASSWORD="${DEMO_PASSWORD:-test123}"
  export DEMO_COMPANY="${DEMO_COMPANY:-FleetWatch}"
  export DEMO_TENANT_ID="${DEMO_TENANT_ID:-tenant_fleetwatch}"
  export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$FLEETWATCH_PORT,http://127.0.0.1:$FLEETWATCH_PORT}"
}

ensure_python_requirements() {
  if python3 - <<'PY' >/dev/null 2>&1
import fastapi  # noqa: F401
import uvicorn  # noqa: F401
import yaml  # noqa: F401
PY
  then
    return
  fi

  log "Installing FleetWatch Python dependencies."
  python3 -m pip install --user --break-system-packages -r "$ROOT_DIR/fleet_api/requirements.txt"
}

build_workspace() {
  log "Building factory inspection packages."
  # shellcheck disable=SC1090
  source "$ROS_SETUP"
  (
    cd "$ROOT_DIR"
    colcon build --symlink-install --packages-select factory_inspection_interfaces factory_inspection_mission
  )
}

write_runner_header() {
  local runner_path="$1"
  cat >"$runner_path" <<EOF
#!/usr/bin/env bash
set -euo pipefail
unset LIBGL_ALWAYS_SOFTWARE || true
unset QT_OPENGL || true
cd $(printf '%q' "$ROOT_DIR")
source $(printf '%q' "$ROS_SETUP")
source $(printf '%q' "$ROOT_DIR/install/setup.bash")
export FACTORY_SCENARIO_SEED=$(printf '%q' "$SCENARIO_SEED")
export FACTORY_BENCHMARK_RUNTIME_ROOT=$(printf '%q' "$FACTORY_BENCHMARK_RUNTIME_ROOT")
export FACTORY_OPERATOR_QUEUE_PATH=$(printf '%q' "$FACTORY_OPERATOR_QUEUE_PATH")
export FLEETWATCH_SQLITE_PATH=$(printf '%q' "$FLEETWATCH_SQLITE_PATH")
export FACTORY_SITE_CONFIG=$(printf '%q' "$FACTORY_SITE_CONFIG")
export FACTORY_ASSET_REGISTRY=$(printf '%q' "$FACTORY_ASSET_REGISTRY")
export FACTORY_INSPECTION_PROFILES=$(printf '%q' "$FACTORY_INSPECTION_PROFILES")
export SECRET_KEY=$(printf '%q' "$SECRET_KEY")
export DEMO_EMAIL=$(printf '%q' "$DEMO_EMAIL")
export DEMO_PASSWORD=$(printf '%q' "$DEMO_PASSWORD")
export DEMO_COMPANY=$(printf '%q' "$DEMO_COMPANY")
export DEMO_TENANT_ID=$(printf '%q' "$DEMO_TENANT_ID")
export CORS_ORIGINS=$(printf '%q' "$CORS_ORIGINS")
EOF
}

create_runner_scripts() {
  mkdir -p "$RUNNER_DIR"

  BENCHMARK_RUNNER="$RUNNER_DIR/benchmark.sh"
  FLEETWATCH_RUNNER="$RUNNER_DIR/fleetwatch.sh"
  SUMMARY_RUNNER="$RUNNER_DIR/patrol_summary.sh"
  ARTIFACTS_RUNNER="$RUNNER_DIR/artifacts_watch.sh"

  write_runner_header "$BENCHMARK_RUNNER"
  cat >>"$BENCHMARK_RUNNER" <<EOF
echo "Launching benchmark with robot_profile=$(printf '%q' "$ROBOT_PROFILE") robot_name=$(printf '%q' "$ROBOT_NAME") seed=$(printf '%q' "$SCENARIO_SEED")"
ros2 launch factory_inspection_mission benchmark_patrol.launch.py \
  headless:=$(printf '%q' "$HEADLESS") \
  use_rviz:=$(printf '%q' "$USE_RVIZ") \
  robot_profile:=$(printf '%q' "$ROBOT_PROFILE") \
  robot_name:=$(printf '%q' "$ROBOT_NAME")
EOF

  write_runner_header "$FLEETWATCH_RUNNER"
  cat >>"$FLEETWATCH_RUNNER" <<EOF
if [[ -f $(printf '%q' "$ROOT_DIR/fleet_api/.env") ]]; then
  set -a
  source $(printf '%q' "$ROOT_DIR/fleet_api/.env")
  set +a
fi
echo "FleetWatch UI: http://localhost:$(printf '%q' "$FLEETWATCH_PORT")/"
echo "FleetWatch API docs: http://localhost:$(printf '%q' "$FLEETWATCH_PORT")/docs"
echo "Demo login: \${DEMO_EMAIL} / \${DEMO_PASSWORD}"
uvicorn fleet_api.app.main:app --host 0.0.0.0 --port $(printf '%q' "$FLEETWATCH_PORT")
EOF

  write_runner_header "$SUMMARY_RUNNER"
  cat >>"$SUMMARY_RUNNER" <<'EOF'
echo "Listening to /patrol_round_summaries"
ros2 topic echo /patrol_round_summaries
EOF

  write_runner_header "$ARTIFACTS_RUNNER"
  cat >>"$ARTIFACTS_RUNNER" <<'EOF'
while true; do
  clear
  printf 'Artifacts Watch  %s\n\n' "$(date)"
  echo "Runtime root: $FACTORY_BENCHMARK_RUNTIME_ROOT"
  echo "Operator queue: $FACTORY_OPERATOR_QUEUE_PATH"
  echo

  echo "Queue snapshot"
  echo "--------------"
  if [[ -f "$FACTORY_OPERATOR_QUEUE_PATH" ]]; then
    sed -n '1,120p' "$FACTORY_OPERATOR_QUEUE_PATH"
  else
    echo "Queue file not created yet."
  fi
  echo

  echo "Latest report summary"
  echo "---------------------"
  if [[ -f "$FACTORY_BENCHMARK_RUNTIME_ROOT/latest_report.json" ]]; then
    python3 - "$FACTORY_BENCHMARK_RUNTIME_ROOT/latest_report.json" <<'PY'
import json
import pathlib
import sys

report_path = pathlib.Path(sys.argv[1])
data = json.loads(report_path.read_text())
for key in [
    "round_number",
    "mission_id",
    "mission_source",
    "mission_type",
    "mission_profile",
    "mission_decision",
    "decision_reason",
    "anomaly_count",
    "critical_count",
    "review_required_count",
    "success",
]:
    print(f"{key}: {data.get(key)}")
print(f"latest_dashboard_html: {report_path.parent / 'latest_dashboard.html'}")
PY
  else
    echo "latest_report.json not created yet."
  fi
  echo

  echo "Recent runtime files"
  echo "--------------------"
  if [[ -d "$FACTORY_BENCHMARK_RUNTIME_ROOT" ]]; then
    find "$FACTORY_BENCHMARK_RUNTIME_ROOT" -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %f\n' 2>/dev/null | sort | tail -n 12
  else
    echo "Runtime directory does not exist yet."
  fi

  sleep 2
done
EOF

  chmod +x "$BENCHMARK_RUNNER" "$FLEETWATCH_RUNNER" "$SUMMARY_RUNNER" "$ARTIFACTS_RUNNER"
}

launch_with_gnome_terminal() {
  local args=()
  args+=(--tab --title="Robot Benchmark" -- bash -lc "$(printf '%q' "$BENCHMARK_RUNNER"); exec bash")
  if [[ "$RUN_FLEETWATCH" == true ]]; then
    args+=(--tab --title="FleetWatch API" -- bash -lc "$(printf '%q' "$FLEETWATCH_RUNNER"); exec bash")
  fi
  if [[ "$RUN_WATCHERS" == true ]]; then
    args+=(--tab --title="Patrol Summary Stream" -- bash -lc "$(printf '%q' "$SUMMARY_RUNNER"); exec bash")
    args+=(--tab --title="Artifacts Watch" -- bash -lc "$(printf '%q' "$ARTIFACTS_RUNNER"); exec bash")
  fi
  gnome-terminal "${args[@]}"
}

launch_with_xterm() {
  xterm -T "Robot Benchmark" -e bash -lc "$(printf '%q' "$BENCHMARK_RUNNER"); exec bash" &
  if [[ "$RUN_FLEETWATCH" == true ]]; then
    xterm -T "FleetWatch API" -e bash -lc "$(printf '%q' "$FLEETWATCH_RUNNER"); exec bash" &
  fi
  if [[ "$RUN_WATCHERS" == true ]]; then
    xterm -T "Patrol Summary Stream" -e bash -lc "$(printf '%q' "$SUMMARY_RUNNER"); exec bash" &
    xterm -T "Artifacts Watch" -e bash -lc "$(printf '%q' "$ARTIFACTS_RUNNER"); exec bash" &
  fi
}

maybe_open_browser() {
  if [[ "$OPEN_BROWSER" != true ]]; then
    return
  fi
  command -v xdg-open >/dev/null 2>&1 || return

  if [[ "$RUN_FLEETWATCH" == true ]]; then
    (
      sleep 5
      xdg-open "http://localhost:$FLEETWATCH_PORT/" >/dev/null 2>&1 || true
    ) &
  fi

  (
    for _ in $(seq 1 180); do
      if [[ -f "$FACTORY_BENCHMARK_RUNTIME_ROOT/latest_dashboard.html" ]]; then
        xdg-open "$FACTORY_BENCHMARK_RUNTIME_ROOT/latest_dashboard.html" >/dev/null 2>&1 || true
        exit 0
      fi
      sleep 2
    done
  ) &
}

print_launch_summary() {
  cat <<EOF

Live demo stack prepared.

What opens:
- Robot benchmark terminal
$( [[ "$RUN_FLEETWATCH" == true ]] && printf '%s\n' '- FleetWatch API terminal' )
$( [[ "$RUN_WATCHERS" == true ]] && printf '%s\n' '- Patrol summary watcher terminal' )
$( [[ "$RUN_WATCHERS" == true ]] && printf '%s\n' '- Artifacts watcher terminal' )

Key paths:
- Runtime root: $FACTORY_BENCHMARK_RUNTIME_ROOT
- Operator queue: $FACTORY_OPERATOR_QUEUE_PATH
- FleetWatch DB: $FLEETWATCH_SQLITE_PATH

FleetWatch:
- UI: http://localhost:$FLEETWATCH_PORT/
- Docs: http://localhost:$FLEETWATCH_PORT/docs
- Demo login: $DEMO_EMAIL / $DEMO_PASSWORD

Generated runners:
- $BENCHMARK_RUNNER
$( [[ "$RUN_FLEETWATCH" == true ]] && printf '%s\n' "- $FLEETWATCH_RUNNER" )
$( [[ "$RUN_WATCHERS" == true ]] && printf '%s\n' "- $SUMMARY_RUNNER" )
$( [[ "$RUN_WATCHERS" == true ]] && printf '%s\n' "- $ARTIFACTS_RUNNER" )
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --headless)
      HEADLESS="True"
      shift
      ;;
    --no-rviz)
      USE_RVIZ="False"
      shift
      ;;
    --skip-build)
      RUN_BUILD=false
      shift
      ;;
    --skip-fleetwatch)
      RUN_FLEETWATCH=false
      shift
      ;;
    --skip-watchers)
      RUN_WATCHERS=false
      shift
      ;;
    --no-browser)
      OPEN_BROWSER=false
      shift
      ;;
    --robot-profile)
      [[ $# -ge 2 ]] || die "--robot-profile requires a value"
      ROBOT_PROFILE="$2"
      shift 2
      ;;
    --robot-name)
      [[ $# -ge 2 ]] || die "--robot-name requires a value"
      ROBOT_NAME="$2"
      shift 2
      ;;
    --seed)
      [[ $# -ge 2 ]] || die "--seed requires a value"
      SCENARIO_SEED="$2"
      shift 2
      ;;
    --fleetwatch-port)
      [[ $# -ge 2 ]] || die "--fleetwatch-port requires a value"
      FLEETWATCH_PORT="$2"
      shift 2
      ;;
    --terminal)
      [[ $# -ge 2 ]] || die "--terminal requires a value"
      TERMINAL_APP="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

require_command bash
require_command python3
require_command colcon
require_command ros2
require_command "$ROOT_DIR/tools/clean_benchmark_runtime.sh"
pick_terminal
load_fleetwatch_env

mkdir -p "$STACK_RUNTIME_DIR"

if [[ "$RUN_BUILD" == true ]]; then
  build_workspace
fi

if [[ "$RUN_FLEETWATCH" == true ]]; then
  ensure_python_requirements
fi

log "Cleaning previous benchmark runtime state."
"$ROOT_DIR/tools/clean_benchmark_runtime.sh"

create_runner_scripts
print_launch_summary

if [[ "$DRY_RUN" == true ]]; then
  exit 0
fi

case "$TERMINAL_APP" in
  gnome-terminal)
    launch_with_gnome_terminal
    ;;
  xterm)
    launch_with_xterm
    ;;
  *)
    die "Unsupported terminal app: $TERMINAL_APP"
    ;;
esac

maybe_open_browser
