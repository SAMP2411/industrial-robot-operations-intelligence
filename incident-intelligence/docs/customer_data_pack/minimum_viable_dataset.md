# Minimum viable dataset

The smallest useful diagnostic normally contains one incident window, a stable asset identifier, timestamps with timezone context, robot or fleet events, one relevant upstream/downstream source, and an operator account of impact and recovery.

- Tier 1 — chronology only: one robot/fleet source plus operator incident/recovery times. Output is explicitly single-source and low-corroboration.
- Tier 2 — cross-system diagnostic: robot/fleet source plus at least one relevant WCS/PLC/door/network/maintenance source and source-clock context.
- Tier 3 — decision-grade candidate: Tier 2 plus business-impact records, recovery actions, product/software versions, expected-source inventory, and an operator available to review the outcome.

Preferred fields are source record ID, event timestamp, asset/system ID, event code/type, severity, message/state transition, software version, and source filename. Supply raw exports rather than screenshots when permitted. The analyst will preview mappings and errors before preservation or normalization.
