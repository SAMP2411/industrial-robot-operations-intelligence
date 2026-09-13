# Phase 2: historical ingestion

Implemented CSV, JSON, JSONL, and structured-text preview/commit; content-addressed original-file storage; SHA-256; safe filenames; type/size checks; reusable mapping profiles; immutable raw records; timestamp normalization; asset matching; unknown-code and duplicate reporting; and idempotency keys.

Verification covers hashing, preview, invalid timestamps, duplicate collapse, MIME rejection, raw immutability, and API ingestion.
