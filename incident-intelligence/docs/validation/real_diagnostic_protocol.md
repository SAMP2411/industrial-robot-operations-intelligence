# Real diagnostic protocol

## Before analysis

Record dataset registration ID/fingerprint, permission, incident scope, expected sources, known outcome (sealed from analyst if feasible), planned hypotheses, success criteria, and stop conditions. Never commit customer data or secrets to Git.

## After analysis

Record import effort, manual mapping/transformation time, generated artifact hashes, analyst conclusion before outcome disclosure, operator review, discrepancies, decision/action supported, corrected conclusion if any, and approved anonymised claim. Calibration requires comparing the pre-disclosure assessment with reviewed outcomes.

Status values: `WAITING_FOR_EXTERNAL_EVIDENCE`, `IN_PROGRESS_PRIVATE`, `REVIEWED`, or `REJECTED`. Repository score increases only from access-controlled, auditable evidence references.
