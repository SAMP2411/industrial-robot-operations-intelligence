# Product definition

## Target user and buyer

The primary user is an automation, maintenance, controls, reliability, or robot-support engineer who must reconstruct a warehouse automation stoppage across systems. The initial buyer is the operations, engineering, maintenance, or integrator leader accountable for downtime and vendor escalation.

## Target incident and pain

The target incident is a robot or automation process that stopped, degraded, or recovered unclearly while evidence was split across robot logs, fleet software, WMS/WCS/WES, PLCs, doors, lifts, chargers, Wi-Fi, tickets, screenshots, and operator notes. Teams lose time collecting evidence, reconciling clocks, debating ownership, and assembling support cases.

## Inputs and outputs

Inputs begin with exported CSV, JSON, JSONL, structured logs, maintenance tickets, ROS-derived neutral events, and analyst notes. Outputs are a cross-system chronology, affected assets, downtime/recovery metrics, evidence quality, reviewed hypotheses, corrective actions, an analyst-approved report, and a selected vendor-support evidence package.

## Why read-only

Brownfield control has safety, production, warranty, and procurement consequences. The product therefore consumes files and read-only/mirrored interfaces. It cannot send navigation goals, allocate work, change PLC/WMS state, or make safety decisions.

## Product boundaries

- A fleet manager controls and allocates robots; this product reconstructs historical incidents.
- A telemetry dashboard shows current signals; this product preserves provenance, aligns sources, measures downtime, and produces a reviewable case.
- Unlike predictive maintenance, which forecasts future failure, this product first explains documented historical disruption.
- Robot inspection gathers condition evidence; this product analyses operational incident evidence from many systems.
