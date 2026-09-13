# Performance and clean-machine status

Chunked upload staging is tested with a generated 50 MB stream and an 8 MB peak-allocation ceiling. Concurrent staging, concurrent ingestion, API load scenarios, retry/fault paths, and report generation are represented in the automated suites and `tests/load/`.

The clean-machine script and both Compose configurations are repository-controlled. CI verifies migrations and PostgreSQL behavior. An independently provisioned target VM has not yet been used for a timed install, load run, encrypted backup/restore drill, or measured RPO/RTO. Those are deployment acceptance items and must be attached to a release record before a customer pilot.
