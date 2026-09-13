# Design Decisions

## Decision 1: One Round Per Nav2 Goal

- Choice: resend the waypoint list after each round
- Why:
  - round boundaries are explicit
  - summaries are natural
  - later mission decisions are clean
- Alternative considered: send repeated waypoints up front
- Why not:
  - blurrier round ownership
  - awkward future inspection and operator logic

## Decision 2: Mission Node In C++

- Choice: C++ over Python
- Why:
  - stronger ROS 2 systems practice
  - better interview signal for robotics roles
  - easy alignment with Nav2 concepts and source-level reading
- Trade-off:
  - slower iteration than Python
- Why acceptable:
  - the project aims for hireable engineering signal, not only fastest prototyping

## Decision 3: Benchmark First, Custom World Later

- Choice: use the Nav2 warehouse benchmark first
- Why:
  - isolate mission logic from custom world issues
  - get a known-good baseline
  - reduce ambiguity during early debugging
- Alternative considered: build the factory world immediately
- Why not:
  - too many moving parts at once

## Decision 4: Inspection In A Waypoint Task Executor Plugin

- Choice: run checkpoint-local inspection in the Nav2 waypoint plugin
- Why:
  - it matches waypoint arrival semantics
  - keeps mission logic clean
  - avoids a separate ad hoc arrival-state machine
- Alternative considered: mission node triggers inspection after every progress update
- Why not:
  - brittle arrival detection
  - bad ownership boundaries

## Decision 5: Controlled Anomalies Before Real Perception

- Choice: configure checkpoint results in YAML first
- Why:
  - repeatable testing
  - fast end-to-end validation
  - easier debugging of mission and reporting layers
- Trade-off:
  - perception is intentionally fake at this stage
- Why acceptable:
  - reliability of system architecture was the priority

## Decision 6: Event-Driven Reporting

- Choice: publish ROS messages and write reports in a subscriber node
- Why:
  - structured interfaces
  - lower coupling
  - easier dashboards and future automation
- Alternative considered: parse console logs or write files directly inside the mission node
- Why not:
  - weak interfaces
  - harder reuse
  - mixed responsibilities

## Decision 7: Severity-Aware Policy Instead Of Simple Boolean Alarm

- Choice: use `normal`, `warning`, and `critical`
- Why:
  - more realistic mission policy
  - supports different operator responses
  - makes the project feel closer to production thinking

## Decision 8: Separate Reporting Artifacts For Different Users

- Choice:
  - JSON for machines
  - Markdown for quick reading
  - HTML dashboard for operator review
- Why:
  - one artifact type is rarely enough
  - different stakeholders consume results differently

## Decision 9: Local Offline Benchmark World

- Choice: vendor benchmark models locally and launch an offline world
- Why:
  - reproducible visual runs
  - fewer external launch-time dependencies
  - stronger benchmark reliability
- Trigger for the change:
  - repeated Fuel download failures blocked visual verification

## Decision 10: Keep Checkpoint Logic In Config

- Choice: checkpoint pose and expected inspection state live in YAML
- Why:
  - easier edits
  - clearer demos
  - no recompile required for route experiments

