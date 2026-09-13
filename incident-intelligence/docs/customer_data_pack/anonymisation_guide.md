# Anonymisation guide

Remove or replace personal names, email addresses, phone numbers, credentials, tokens, internal public-facing secrets, unrelated IP/MAC addresses, order/customer identifiers, and free-text unrelated to the incident. Keep replacements consistent so cross-source joins remain possible. Preserve timestamps only to the precision needed; a consistent deterministic offset is preferable to deleting them.

Do not alter event order, event codes, state transitions, durations, or asset relationships. Keep an internal customer-held mapping if re-identification is required. `scripts/anonymize_dataset.py` offers deterministic identifiers and emits a manifest; the customer should review its output before transfer.
