# Autonomous Factory Inspection Robot Dossier

This folder is the project record for the `Autonomous Factory Inspection Robot` portfolio build. It is meant to answer four questions clearly:

1. What was the goal?
2. What was built in each phase?
3. How was it verified?
4. How would you explain it in an interview?

## Project Snapshot

- Project: ROS 2 / Nav2 autonomous mobile robot for repeated factory patrol and checkpoint inspection
- Current state: adaptive asset-centric patrol with multimodal inspection, saved evidence, RViz anomaly markers, structured reports, dashboard artifact, round-level safety policy, targeted follow-up rounds, and campaign-state history
- Core benchmark: Nav2 warehouse map with a local offline world and controlled inspection labels
- Main benchmark outcomes:
  - April 5, 2026: `Round 1 summary: duration=44.844s, action_result=SUCCEEDED, nav2_error_code=0, missed=[], inspections=5, anomalies=2, warnings=1, critical=1, capture_failures=0, decision=HOLD`
  - April 6, 2026: `Round 1 summary: duration=82.407s, action_result=SUCCEEDED, nav2_error_code=0, phase=routine, inspections=5, anomalies=2, warnings=2, critical=0, decision=TARGETED_FOLLOW_UP`, followed automatically by a focused 2-asset rescan

## How To Use This Folder

- Start with [../README.md](../README.md) if you want the full documentation map first.
- Start with [01_project_pitch_and_scope.md](01_project_pitch_and_scope.md) if you want the big picture.
- Read [02_phase_1_navigation_mvp.md](02_phase_1_navigation_mvp.md) through [05_phase_4_safety_and_reliability.md](05_phase_4_safety_and_reliability.md) to understand the build history in order.
- Read [06_design_decisions.md](06_design_decisions.md) if you need reasoning and trade-offs.
- Read [07_concepts_basic_to_advanced.md](07_concepts_basic_to_advanced.md) if you want the concepts taught from beginner to advanced.
- Read [08_complete_workflow.md](08_complete_workflow.md) when you want to run, verify, or extend the system.
- Read [../PIPELINE_WORKFLOW_FOR_BEGINNERS.md](../PIPELINE_WORKFLOW_FOR_BEGINNERS.md) if you want a simpler "start here" explanation of how the pipeline works from launch to reports.
- Read [../ITERATION_TESTING_README.md](../ITERATION_TESTING_README.md) when you want the shortest safe command loop for daily testing and maintenance.
- Read [09_verification_log.md](09_verification_log.md) for proof checkpoints and exact observed outputs.
- Read [10_codebase_file_guide.md](10_codebase_file_guide.md) when you want a guided code tour.
- Read [11_interview_questions_and_answers.md](11_interview_questions_and_answers.md) before presentations or hiring loops.
- Read [12_issues_debugging_and_fixes.md](12_issues_debugging_and_fixes.md) for failure patterns and fixes.
- Read [13_results_gallery.md](13_results_gallery.md) for screenshots and artifacts.
- Read [14_enterprise_inspired_upgrades.md](14_enterprise_inspired_upgrades.md) and [15_adaptive_follow_up_campaigns.md](15_adaptive_follow_up_campaigns.md) for the more product-style phases.
- Read [16_hardening_and_regression.md](16_hardening_and_regression.md) for the reliability and verification hardening pass.

## Folder Map

```text
docs/project_dossier/
├── README.md
├── 01_project_pitch_and_scope.md
├── 02_phase_1_navigation_mvp.md
├── 03_phase_2_inspection_mvp.md
├── 04_phase_3_reporting_and_visualization.md
├── 05_phase_4_safety_and_reliability.md
├── 06_design_decisions.md
├── 07_concepts_basic_to_advanced.md
├── 08_complete_workflow.md
├── 09_verification_log.md
├── 10_codebase_file_guide.md
├── 11_interview_questions_and_answers.md
├── 12_issues_debugging_and_fixes.md
├── 13_results_gallery.md
├── 14_enterprise_inspired_upgrades.md
├── 15_adaptive_follow_up_campaigns.md
├── 16_hardening_and_regression.md
└── assets/
    ├── evidence/
    ├── results/
    └── visuals/
```

## Asset Guide

- `assets/visuals/` contains screenshots from the visual benchmark run.
- `assets/evidence/` contains saved checkpoint inspection images.
- `assets/results/` contains copied benchmark artifacts such as JSON, Markdown, HTML, and CSV outputs.

## Recommended Reading Order For Reviewers

1. `README.md`
2. `01_project_pitch_and_scope.md`
3. `06_design_decisions.md`
4. `09_verification_log.md`
5. `13_results_gallery.md`
6. `15_adaptive_follow_up_campaigns.md`
7. `16_hardening_and_regression.md`

## Recommended Reading Order For Me

1. `01_project_pitch_and_scope.md`
2. `02_phase_1_navigation_mvp.md`
3. `03_phase_2_inspection_mvp.md`
4. `04_phase_3_reporting_and_visualization.md`
5. `05_phase_4_safety_and_reliability.md`
6. `10_codebase_file_guide.md`
7. `11_interview_questions_and_answers.md`
8. `14_enterprise_inspired_upgrades.md`
9. `15_adaptive_follow_up_campaigns.md`
10. `16_hardening_and_regression.md`
