# Update policy

Pilot deployments pin a repository commit and container image digest. Security and dependency updates are tested through unit, contract, integration, security, end-to-end, migration, and Compose health checks before rollout. Database backups and restore verification precede schema-affecting upgrades. Rollback uses the previous image plus a migration-compatible database; destructive downgrades require a reviewed restore plan.
