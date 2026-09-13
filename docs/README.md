# Documentation Hub

All project documentation now lives under this `docs/` folder.

Use this file as the map.

## Best Starting Points

- Startup handoff summary:
  [`STARTUP_CONTEXT_SUMMARY.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/STARTUP_CONTEXT_SUMMARY.md)
- Beginner-friendly pipeline guide:
  [`PIPELINE_WORKFLOW_FOR_BEGINNERS.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/PIPELINE_WORKFLOW_FOR_BEGINNERS.md)
- Short daily test workflow:
  [`ITERATION_TESTING_README.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/ITERATION_TESTING_README.md)
- Full project dossier:
  [`project_dossier/README.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/project_dossier/README.md)
- Living engineering notes:
  [`engineering_manual.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/engineering_manual.md)
- Current-state audit docs:
  [`current_architecture.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/current_architecture.md)
- Current output schema map:
  [`current_output_schemas.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/current_output_schemas.md)
- Operator console README:
  [`fleet_api/README.md`](/home/samarth/projects/industrial-robot-operations-intelligence/fleet_api/README.md)
- Phase reports:
  [`phase_00_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_00_report.md)
  and
  [`phase_01_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_01_report.md)
  and
  [`phase_04_report.md`](/home/samarth/projects/industrial-robot-operations-intelligence/docs/phase_reports/phase_04_report.md)

## Folder Layout

```text
docs/
├── README.md
├── STARTUP_CONTEXT_SUMMARY.md
├── PIPELINE_WORKFLOW_FOR_BEGINNERS.md
├── ITERATION_TESTING_README.md
├── engineering_manual.md
├── current_architecture.md
├── current_topic_graph.md
├── current_launch_flow.md
├── current_data_outputs.md
├── current_output_schemas.md
├── current_known_limitations.md
├── current_package_dependency_graph.md
├── current_test_inventory.md
├── current_risks_and_migration_plan.md
├── phase_reports/
│   ├── phase_00_report.md
│   └── phase_01_report.md
├── fleet_api/
│   └── README.md
├── project_dossier/
│   ├── README.md
│   ├── 01_project_pitch_and_scope.md
│   ├── ...
│   └── assets/
└── private/
    └── START_HERE_STUDY_GUIDE.md
```

## What Each Area Is For

### `PIPELINE_WORKFLOW_FOR_BEGINNERS.md`

Simple explanation of the system from launch file to reports.

### `ITERATION_TESTING_README.md`

Shortest safe command loop for building, testing, and checking health after each change.

### `engineering_manual.md`

Living notebook of concepts, debugging lessons, and project evolution.

### `STARTUP_CONTEXT_SUMMARY.md`

Simple handoff document for external AI chats, mentors, startup planning, or collaborators.

### `current_*.md`

Repository-inspection-based audit documents describing the system as it exists today.

### `current_output_schemas.md`

Quick map of the current YAML/JSON/CSV export contracts and where their schema versions come from.

### `phase_reports/`

Phase-by-phase engineering change records tied to real verification steps.

### `fleet_api/README.md`

Developer-facing guide for the new FleetWatch operator console and inspection workflow.

### `project_dossier/`

Public-facing project record:

- phases
- design decisions
- verification logs
- interview prep
- code tour
- artifacts

### `private/`

Local-only notes for personal study and memory refresh.

This folder is intentionally ignored by Git.
