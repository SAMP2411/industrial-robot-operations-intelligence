# Data retention

Retention is configured per diagnostic agreement. Collect only sources relevant to the incident, avoid worker-identifying data by default, redact it when possible, restrict access separately when required, and exclude it from vendor packages unless explicitly necessary and approved.

Raw evidence is immutable during the engagement. Deletion after the agreed retention period is an administrative, audited operation performed at the storage/database layer under a reviewed procedure; the MVP intentionally exposes no casual raw-record delete endpoint. Backups follow the same retention and access rules.
