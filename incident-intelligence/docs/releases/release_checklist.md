# Release checklist

- [ ] Scope and product-claim lint pass.
- [ ] Unit, property, connector contract, integration, security, browser, fault, migration, and end-to-end suites pass.
- [ ] PostgreSQL CI result passes.
- [ ] Scorecard and private-data scanner pass.
- [ ] Dependency, static, secret, and container scans have no unaccepted critical findings.
- [ ] CycloneDX SBOM and release manifest are attached.
- [ ] Alembic upgrade/downgrade/upgrade test passes.
- [ ] Backup and isolated restore drill is timed and recorded for the target deployment.
- [ ] Compose configuration and health checks pass on a clean machine.
- [ ] Load profile is within the agreed pilot capacity.
- [ ] Customer security questions and residual risks are accepted.
- [ ] Synthetic/demo artifacts are labelled; customer artifacts have approval and redaction evidence.
- [ ] Version, migration notes, rollback owner, release approver, and hashes are recorded.

Automation is provided by `scripts/release_gate.py`, CI workflows, `scripts/clean_machine_verify.sh`, and `tests/load/`. A checked box requires the referenced run; repository presence alone is not execution evidence.
