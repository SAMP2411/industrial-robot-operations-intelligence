#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${FACTORY_REGRESSION_RESULTS_DIR:-$HOME/.ros/factory_inspection/benchmark/regression}"
SEEDS=("$@")

if [[ "${#SEEDS[@]}" -eq 0 ]]; then
  SEEDS=(4242 5151 6262)
fi

mkdir -p "$RESULTS_DIR"
summary_csv="$RESULTS_DIR/regression_summary.csv"
echo "seed,round_number,mission_decision,accuracy_percent,precision_percent,recall_percent,f1_percent,anomaly_count,follow_up_assets" >"$summary_csv"

for seed in "${SEEDS[@]}"; do
  echo "Running benchmark regression seed $seed"
  export FACTORY_SCENARIO_SEED="$seed"
  export FACTORY_SCENARIO_ALLOW_CRITICAL="${FACTORY_SCENARIO_ALLOW_CRITICAL:-false}"
  export FACTORY_SCENARIO_MIN_ANOMALIES="${FACTORY_SCENARIO_MIN_ANOMALIES:-2}"
  export FACTORY_SCENARIO_MAX_ANOMALIES="${FACTORY_SCENARIO_MAX_ANOMALIES:-2}"

  "$ROOT_DIR/tools/run_benchmark_with_retry.sh" headless:=True use_rviz:=False

  report_path="$HOME/.ros/factory_inspection/benchmark/latest_report.json"
  row="$(jq -r --arg seed "$seed" '[
      $seed,
      .round_number,
      .mission_decision,
      .accuracy_percent,
      .precision_percent,
      .recall_percent,
      .f1_percent,
      .anomaly_count,
      (.follow_up_assets | join("|"))
    ] | @csv' "$report_path")"
  echo "$row" >>"$summary_csv"
done

echo "Regression summary written to $summary_csv"
