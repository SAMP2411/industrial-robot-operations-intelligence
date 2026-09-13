# Enterprise-Inspired Upgrades

## Why This Phase Exists

This phase pushes the project closer to the kind of product behavior seen in industrial inspection platforms:

- assets, not just waypoints
- multimodal inspection, not camera-only labels
- prioritized follow-up, not only patrol completion
- operator-facing dashboards, not only logs
- targeted asset missions, not only full patrol loops

The goal is not to claim enterprise parity. The goal is to show portfolio-grade architecture that scales in the same direction.

## What Was Added

### 1. Asset Registry in Mission Config

Each checkpoint now carries:

- `asset_id`
- `asset_display_name`
- `asset_type`
- `zone`
- `asset_priority`
- `enabled_modalities`

Why it matters:

- the robot can explain *which industrial asset* was inspected
- reports read like operations tooling instead of debug output
- interview answers can connect robotics behavior to plant operations language

### 2. Multimodal Inspection Result

Each inspection result now includes:

- visual label and severity
- thermal delta
- acoustic level
- gas concentration
- anomaly source list
- asset health score
- asset status

Why it matters:

- one checkpoint can now produce a richer maintenance assessment
- mission policy can react to risk, not just a boolean anomaly
- dashboards can prioritize follow-up assets

### 3. Targeted Follow-Up Profile

The benchmark can now run in two modes:

- `routine_autonomous_round`
- `targeted_follow_up`

`FACTORY_TARGET_ASSETS` filters the generated route to only the selected assets.

Why it matters:

- this approximates the real operator workflow of “inspect these assets now”
- it demonstrates that route generation and mission behavior can change without rewriting Nav2

### 4. Digital Twin Style Dashboard

The HTML dashboard now includes:

- summary tiles
- zone summary cards
- prioritized asset cards
- a lightweight site-map SVG
- evidence images per asset

Why it matters:

- it gives the project a product layer, not only an engineering layer
- it makes results legible to recruiters, operators, and teammates

### 5. Unique Run Identity

Every generated scenario now has a unique `run_id`.

Why it matters:

- repeated reruns of the same seed no longer mix report data
- report integrity is preserved during iterative development

### 6. Review Queue and Confidence

The inspection result stream now includes:

- inspection confidence
- review-required flag
- review reason
- raw evidence path
- annotated evidence path

Why it matters:

- the robot no longer has to choose only between “anomaly” and “nominal”
- weak visual-only findings can be routed into a review queue instead of becoming false alarms
- the saved evidence is more explainable during debugging and interviews

### 7. Run-Scoped Artifact Archive

Reports are now written to both:

- the legacy latest files for convenience
- a run-specific folder under `~/.ros/factory_inspection/benchmark/<run_id>/`

Why it matters:

- every patrol round now has an audit trail that survives later reruns
- benchmark screenshots, HTML dashboards, and JSON outputs are easier to compare across iterations

## Verified Outcome

Verified on April 5, 2026:

- the upgraded benchmark completed a full `routine_autonomous_round`
- the robot saved 5 inspection images
- the mission produced a `HOLD` on a critical asset
- the report JSON and dashboard both reflected the same asset set
- `inspection_count` matched the number of checkpoint entries in the report after the `run_id` fix
- after the review-policy upgrade, `FACTORY_SCENARIO_SEED=4242` and `FACTORY_SCENARIO_SEED=5151` both completed with `accuracy=100%`, `false_positive_count=0`, and a low-confidence conveyor hit demoted to `unconfirmed_visual_finding`

## Honest Gaps

This phase is still a portfolio system, not a deployed enterprise robot platform.

Current gaps:

- multimodal non-visual channels are simulated benchmark signals, not real sensor topics
- the visual classifier still uses lightweight heuristics plus asset-type confirmation policy, not a trained perception model
- targeted follow-up is route-generation based, not a live UI-driven dispatch tool
- the project has one benchmark world, not a full fleet/site backend

## Interview Framing

Strong one-liner:

> I evolved the project from a waypoint demo into an asset-centric inspection system with multimodal anomaly fusion, targeted follow-up missions, prioritized reporting, and operator-facing dashboards.

Strong architecture answer:

> Nav2 still owns motion, but the mission layer owns patrol rounds and policy, and the waypoint task executor owns checkpoint-local inspection fusion. That separation made it possible to add richer inspection and reporting without destabilizing navigation.
