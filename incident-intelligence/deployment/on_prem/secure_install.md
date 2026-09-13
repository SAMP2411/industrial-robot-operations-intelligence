# Secure on-premises installation

This profile is a pilot baseline, not a universal production certification.

1. Provision a dedicated patched Linux host, DNS name, restricted firewall, persistent database/evidence/backup volumes, and a secrets source outside Git.
2. Copy `.env.example` to a protected deployment-specific environment file. Set a strong database password, `RFII_AUTH_MODE=oidc` with the customer identity provider, upload/retention limits, and a 32-byte evidence key supplied through the deployment secret mechanism.
3. Configure the domain in `deployment/on_prem/Caddyfile` and inspect `docker compose -f docker-compose.yml -f docker-compose.secure.yml config`.
4. Start the stack, apply migrations, and check `/health/live`, `/health/ready`, and authenticated `/metrics` access according to the network policy.
5. Run `deployment/on_prem/backup.sh`, restore into an isolated database with `deployment/on_prem/restore.sh`, record timing, and retain the drill evidence.
6. Run `scripts/release_gate.py` and the customer security checklist before admitting customer data.

Only ports 80/443 should be externally reachable. PostgreSQL and application ports remain on the internal Compose network. Terminate TLS at Caddy or an approved customer reverse proxy. Rotate identity, database, TLS, and evidence-encryption secrets under the customer change process; retain old evidence keys until all dependent evidence has been re-encrypted or expired.

Recovery objectives are deployment agreements, not code guarantees. Measure and record actual RPO/RTO in every restore drill.
