# Security architecture

The product is read-only toward customer operational systems. Generic connectors declare only read/export permissions and cannot write to robots, WMS/WCS, PLCs, or fleet managers.

Pilot authentication uses salted scrypt password hashes, HMAC-SHA256 signed expiring bearer tokens, token-version revocation, account disablement, and one-time hashed reset tokens. Roles are `admin`, `analyst`, `reviewer`, `operator`, `partner`, and `viewer`; permission checks cover reads, writes, uploads, approval, and administration. A single-customer on-prem deployment is the supported pilot boundary; cross-customer SaaS tenancy is not claimed.

Uploads are basename-normalized, extension allow-listed, MIME checked, size limited, UTF-8 parsed, and stored outside served paths. API responses never expose evidence storage paths. Original bytes and raw payloads are retained; spreadsheet-leading formula characters are neutralized only in generated CSV exports.

Raw records and audit events reject application updates/deletes. Approved report artifacts reject later mutation. Important actions record actor, action, entity, detail, and timestamp.

Secrets are environment variables and `.env` is ignored. Docker runs the application as an unprivileged user. TLS is expected at the customer-controlled reverse proxy. Database/evidence volume encryption depends on the host or customer storage platform and must be confirmed during the security review.
