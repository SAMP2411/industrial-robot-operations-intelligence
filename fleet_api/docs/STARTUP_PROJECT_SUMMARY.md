# FleetWatch Startup Project Summary

**Document purpose:** This is the current plain-language summary of the FleetWatch service as it exists inside the robotics repo on **Saturday, July 18, 2026**.

It is written so you can paste it into another AI chat, mentor discussion, or startup planning conversation without forcing that person to inspect the whole codebase first.

## 1. Executive Summary

FleetWatch began as a multi-tenant robot fleet observability MVP built with FastAPI, InfluxDB, a simple web dashboard, and a telemetry simulator.

In this repo it has now been advanced into a broader **operator console** for the `Autonomous Factory Inspection Robot` project.

Today it has two product roles:

1. **Fleet observability**
   - optional InfluxDB-backed robot telemetry
   - robot health and fault visibility
   - fleet KPI summaries

2. **Inspection operations**
   - sync the latest ROS 2 factory inspection benchmark artifacts into SQLite
   - expose sites, assets, missions, evidence metadata, and findings through an authenticated API
   - let an operator acknowledge, assign, reinspect, resolve, and close findings from a web UI

So the service is no longer only “a robot monitoring dashboard.”

It is now the first operator-facing workflow layer for the factory inspection platform.

## 2. What Problem This Solves

The robot benchmark was already generating good outputs:

- `latest_report.json`
- `latest_campaign_state.json`
- `inspection_log.csv`
- evidence images

But an operator still had to open those files manually.

FleetWatch now solves that gap by turning exported benchmark artifacts into:

- a findings queue
- an asset-centric view
- a mission queue
- an evidence preview workflow
- a persistent local audit trail for operator actions

That directly addresses the next startup-grade step from `docs/advance.md`: move from file outputs to operator-usable workflow.

## 3. Current Product Scope

### 3.1 Fleet observability scope

When InfluxDB is configured, FleetWatch still provides:

- tenant-scoped robot list
- fleet uptime
- average battery
- total tasks
- active fault count
- recent fault log
- simulated AMR telemetry for demo purposes

### 3.2 Inspection operator scope

FleetWatch now also provides:

- benchmark sync from ROS artifact files
- SQLite-backed persistence
- site list
- asset list
- mission queue
- findings queue
- evidence metadata lookup
- browser-based evidence preview
- finding lifecycle actions

## 4. Current Architecture

```text
ROS 2 / Nav2 benchmark
        |
        | generates reports, campaign state, evidence, scenario files
        v
FleetWatch benchmark sync
        |
        v
SQLite operator store
        |
        +--> FastAPI operator API
        |
        +--> FleetWatch web console

Optional side path:

Robot simulator / robot agent
        |
        v
    InfluxDB
        |
        +--> FastAPI fleet APIs
        +--> FleetWatch fleet panels
        +--> Grafana
```

## 5. Current Data Model

The operator database now persists:

- users
- tenant robot mappings
- sites
- assets
- missions
- evidence metadata
- findings
- finding events
- sync history

This is the first real persistent operations layer in the repo.

## 6. Current Operator Workflow

1. The operator signs in to the FleetWatch console.
2. They click `Sync latest benchmark`.
3. FleetWatch loads:
   - site config
   - asset registry
   - inspection profile config
   - scenario manifest
   - campaign state
   - round reports
4. That data is persisted into SQLite.
5. The console shows:
   - site overview
   - assets
   - findings
   - missions
   - evidence preview
   - system health
6. The operator can then:
   - acknowledge a finding
   - assign it
   - request reinspection
   - resolve it
   - close it

This is the first time the project supports a workflow that does not require opening raw result files manually.

## 7. Current Strengths

- the service still preserves the original fleet telemetry idea
- the UI is now much more useful for the inspection project itself
- SQLite persistence makes the workflow stateful
- the benchmark sync path is deterministic and explainable
- the operator API is versioned under `/api/v1`
- there is now an automated API regression test for the finding lifecycle

## 8. Current Limitations

- the inspection workflow still syncs from exported files rather than receiving live runtime events
- operator-created missions are not yet pushed back into live ROS mission execution
- authorization is tenant-level JWT auth, not a full production permission system
- telemetry and inspection operations still share one local MVP service
- Influx-backed fleet visibility remains optional and environment-dependent

## 9. Why This Matters For The Startup Story

Before this step, the robotics project had:

- robot autonomy
- inspection logic
- evidence generation
- report exports

After this step, it also has:

- operator state
- persisted findings
- operator actions
- a mission queue concept
- a browser workflow for triage

That is a real jump from “technical prototype” toward “operator-usable product foundation.”

## 10. Honest Maturity Label

Current maturity:

> Local integrated MVP for fleet observability plus inspection operations.

Not yet:

- production SaaS
- live mission orchestration platform
- hardened multi-user control room software
- validated commercial product

But it is now much closer to startup-grade workflow architecture than the original standalone dashboard.
