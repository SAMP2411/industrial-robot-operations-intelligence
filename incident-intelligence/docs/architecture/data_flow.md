# Data flow

1. An analyst creates a diagnostic engagement and registers expected data sources.
2. A file is read within the configured size limit. Preview detects columns, timestamp interpretation, samples, proposed asset mappings, errors, skipped records, and unknown codes without persistence.
3. Explicit upload preserves original bytes under a content-addressed path with filename, MIME type, size, SHA-256, uploader audit event, and engagement/source identity.
4. Explicit commit creates immutable raw records. Duplicate payloads within a run are collapsed and repeated idempotency keys return the existing run.
5. Each accepted raw record produces a canonical event retaining raw identity, original and UTC time, time quality, applied clock offset, normalized severity, asset mapping, and unknown attributes.
6. An incident window selects events from all engagement sources. Filters and analyst clock offsets produce deterministic ordering; annotations and recovery actions join the timeline.
7. Downtime, data-quality, hypotheses, and evidence relations remain editable until human review.
8. Report generation reads stored structured data. A vendor package includes only raw records explicitly selected by the analyst and emits a hash manifest.
9. Approval records the reviewer and time and makes that report version immutable. Regeneration creates a new version.
