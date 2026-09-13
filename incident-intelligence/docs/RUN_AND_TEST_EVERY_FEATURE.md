# Run and test every feature

This runbook takes a tester from a clean checkout through the complete Robot Fleet Incident Intelligence workflow. It uses only synthetic fixtures. Complete the stages in order because later stages reuse records created earlier.

The required path is the incident-intelligence product in `apps/`, `packages/`, and `connectors/`. The preserved ROS 2 autonomy demo under `legacy/` is optional and is tested separately in Stage 16.

## How to use this guide

- Run shell commands from the repository root unless a stage says otherwise.
- Keep **Terminal A** running the API and use **Terminal B** for commands.
- Use a dedicated manual-test database and storage directory. This prevents test data from mixing with normal development data.
- Record each stage as pass, fail, or skipped in the checklist below. Do not mark a stage passed unless both its visible result and checkpoint test pass.
- Replace values such as `<incident-id>` only where angle brackets are shown. Shell variables such as `$INCIDENT_ID` are populated by the commands in the preceding stages.
- `jq` is used to read JSON and capture IDs. Install it with your operating system package manager if `jq --version` fails.
- Never use real customer exports for this walkthrough. The retention exercise permanently removes its disposable test engagement.

## Completion checklist

| Stage | Feature area | Result | Notes |
|---|---|---|---|
| 0 | Prerequisites and isolated environment | [ ] | |
| 1 | Automated baseline | [ ] | |
| 2 | API, console, health, OpenAPI, metrics | [ ] | |
| 3 | Engagement intake and privacy controls | [ ] | |
| 4 | CSV/JSON/JSONL preview, preservation, commit, errors | [ ] | |
| 5 | Assets, mapping decisions, mapping profiles | [ ] | |
| 6 | Incident, timeline, provenance, clock and boundaries | [ ] | |
| 7 | Downtime, recovery, lifecycle, grouping and metrics | [ ] | |
| 8 | Hypotheses, evidence, quality and review gates | [ ] | |
| 9 | Reports, redaction, approval, comparison and vendor ZIP | [ ] | |
| 10 | Authentication, roles, tenant isolation, audit and rate limits | [ ] | |
| 11 | Private-dataset registry, reuse measurement and validation evidence | [ ] | |
| 12 | Retention and independently approved deletion | [ ] | |
| 13 | PostgreSQL, worker and Docker deployment | [ ] | |
| 14 | Backup/restore, reliability, security and release gates | [ ] | |
| 15 | Full regression | [ ] | |
| 16 | Optional legacy autonomy demo | [ ] | |

## Stage 0 — prerequisites and isolated environment

Required: Python 3.11 or newer, Git, and `curl`. Docker is required only for Stages 13–14. A Chromium-compatible browser is required for browser tests.

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
python3 --version
git --version
curl --version
jq --version
git status --short
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[postgres,test]'
python -m playwright install chromium
```

Browser tests use `/usr/bin/google-chrome` by default. If Chrome/Chromium lives elsewhere, export its absolute executable path as `CHROME_BIN` before running pytest. On Linux, `python -m playwright install --with-deps chromium` can install a browser and OS libraries but requires administrator access; set `CHROME_BIN` to that installed browser because the test harness does not guess its location.

Create isolated local settings in every terminal used for Stages 1–12:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence
source .venv/bin/activate
mkdir -p storage/manual-test
export RFII_DATABASE_URL='sqlite:////home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/storage/manual-test.db'
export RFII_STORAGE_ROOT='/home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/storage/manual-test'
export RFII_AUTH_REQUIRED='false'
export RFII_APP_ENV='development'
export RFII_SECRET_KEY='manual-test-secret-at-least-32-characters'
python -m alembic upgrade head
```

Expected result: Alembic reaches the current head without an error and `storage/manual-test.db` exists.

To resume on another day, repeat only the `cd`, activation, and `export` commands. The database preserves completed stages.

## Stage 1 — automated baseline

Run the fast contracts and core domain tests before manual testing:

```bash
python -m pytest \
  tests/contract \
  tests/unit \
  tests/property \
  tests/connector_contract \
  -q
```

Expected result: all collected tests pass. These tests cover product-scope invariants, OpenAPI shape, streamed ingestion, anonymisation, timing, evidence scoring, buyer outputs, connector certification, and scorecard evidence.

If this stage fails, stop and save the full output with:

```bash
python -m pytest tests/contract tests/unit tests/property tests/connector_contract -vv | tee storage/manual-test/stage-01.log
```

## Stage 2 — API, console, health, OpenAPI, and metrics

In **Terminal A**, apply the Stage 0 environment and start the server:

```bash
uvicorn apps.diagnostic_api.main:app --reload --host 127.0.0.1 --port 8000
```

In **Terminal B**, apply the Stage 0 environment and run:

```bash
export API='http://127.0.0.1:8000'
curl -fsS "$API/health" | jq
curl -fsS "$API/openapi.json" | jq '.info, (.paths | length)'
curl -fsS -H 'X-Role: admin' -H 'X-Actor: stage-tester' "$API/metrics" | head
```

Expected results:

- health returns a healthy status and database/storage checks;
- OpenAPI returns application metadata and a non-zero path count;
- metrics contains Prometheus text such as request or process metrics.

Open these pages in a browser:

- console: <http://127.0.0.1:8000/>
- interactive API: <http://127.0.0.1:8000/docs>
- raw health response: <http://127.0.0.1:8000/health>

The console should show `Local analyst mode`, the main navigation, and `Read-only toward operational systems`.

Checkpoint:

```bash
python -m pytest tests/contract/test_openapi.py tests/integration/test_console_workflow.py -q
```

## Stage 3 — engagement intake and privacy controls

In the browser, open **Engagements** and create this synthetic engagement:

| Field | Value |
|---|---|
| Customer name | Synthetic Robotics GmbH |
| Site name | Berlin Test Lab |
| Site timezone | UTC |
| Incident/engagement title | Door and Wi-Fi ambiguity |
| Approximate incident window | 2026-04-07 09:12–09:16 UTC |
| Expected sources | robot/fleet log, external system log, network/PLC export |
| Handling basis | Synthetic or permitted export |
| Permission and data scope | checked |

Click **Review and create**. Expected result: the console reports that the engagement was created and moves to **Upload & preview**. Return to **Engagements** and confirm it is listed.

Also verify draft protection: begin typing a different customer name, refresh, and confirm it is restored. Clear the draft afterwards. This exercises the browser's unfinished-work safeguard.

Checkpoint:

```bash
python -m pytest tests/browser/test_engagement_wizard.py tests/security/test_private_data_guard.py -q
```

## Stage 4 — preview, preserve, and ingest every supported format

The workflow has three deliberate steps: preview does not store evidence, preserve stores the exact source bytes and SHA-256, and commit creates immutable raw records plus canonical events.

For each row below, open **Upload & preview**, register the source, select its file, click **Preview—no import**, inspect detected columns/sample/errors, then click **Preserve file** and **Commit ingestion**.

| Source name | Source type | Offset | File | Expected records |
|---|---|---:|---|---:|
| Robot controller | robot_controller | 0 | `fixtures/incident_001_door_wifi/robot.csv` | 4 |
| Fleet manager | fleet_manager | 0 | `fixtures/incident_001_door_wifi/fleet.json` | 3 |
| Door and Wi-Fi infrastructure | infrastructure | 3400 | `fixtures/incident_001_door_wifi/door_wifi.jsonl` | 3 |

Use timezone `UTC`. Leave encoding on auto-detect and mapping YAML blank for these canonical fixtures. Expected result after each commit: the status reports the same number of raw records and normalized events as the table.

### Malformed rows and declarative mapping

Register a fourth source named `Malformed mapping exercise`, type `robot_log`. Choose `fixtures/malformed_sources/first_sprint_robot_events.csv`, paste the contents of `fixtures/malformed_sources/generic_robot_error_mapping.yaml` into **Mapping profile YAML**, and preview it.

Expected result: preview exposes the invalid timestamp and duplicate/unusual input without crashing. Use **Download row-error CSV** and inspect the downloaded file. This proves bad rows are visible rather than silently discarded. You may preserve and commit this source; its valid rows remain usable.

### Encoding and ZIP safety

The UI supports explicit UTF-8, UTF-8 BOM, Windows-1252, and ISO-8859-1 overrides. The automated hardening tests create representative encodings and hostile archives. Run:

```bash
python -m pytest \
  tests/unit/test_ingestion.py \
  tests/unit/test_ingestion_hardening.py \
  tests/fuzz/test_parser_fuzz.py \
  tests/integration/test_api_ingestion.py \
  tests/integration/test_ingestion_profiles.py \
  -q
```

Optional positive ZIP UI check:

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

target = Path('storage/manual-test/safe-evidence.zip')
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    archive.write('fixtures/incident_001_door_wifi/robot.csv', 'robot.csv')
print(target)
PY
```

Upload that file under **Optional ZIP evidence bundle**. Expected result: one file is validated and the archive SHA-256 is shown. Do not extract untrusted ZIPs yourself; the application rejects traversal, links, encrypted content, nested archives, and archive bombs.

Browser checkpoint:

```bash
python -m pytest tests/browser/test_upload_preview_commit.py -q
```

## Stage 5 — assets, mappings, and immutable profiles

Open **Mapping review**. Create these assets for Berlin Test Lab:

| Name | External ID | Type |
|---|---|---|
| Robot 07 | AMR-07 | amr |
| Door 04 | DOOR-04 | door |
| Wi-Fi Zone A | WIFI-ZONE-A | network_zone |

For each external ID, save an audited mapping decision using `analyst_confirmation` and a concrete rationale such as `Confirmed against the synthetic fixture manifest`. Confirm all three appear in **Mapping history**. Leave `AMR-09` or `AMR-12` unresolved once to exercise the explicit unresolved state.

Open **Mapping profiles** and save:

| Field | Value |
|---|---|
| Profile name | Generic robot event export |
| Version | 1.0 |
| Source type | robot_log |
| Test fixture | fixtures/malformed_sources/first_sprint_robot_events.csv |
| Compatibility notes | Synthetic canonical columns; UTC timestamps |

Keep the prefilled constrained YAML. Save another version as `1.1` to verify profiles are versioned instead of overwritten.

The browser intentionally focuses on analyst mapping. System records, dependencies, aliases, and the legacy YAML registry adapter are covered by API/domain tests:

```bash
python -m pytest tests/browser/test_mapping_review.py tests/contract/test_connectors.py tests/connector_contract -q
```

Expected result: all tests pass and the UI retains both profile versions.

### Registry relationships and aliases

The console creates assets; the relationship model is tested through the API. Capture the relevant IDs and add a system, alias, and dependency:

```bash
export API='http://127.0.0.1:8000'
export ADMIN_HEADER='X-Role: admin'
export ACTOR_HEADER='X-Actor: stage-admin'
SITE_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/sites" | jq -r '.items[] | select(.name=="Berlin Test Lab") | .id' | head -n1)
ROBOT_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/assets" | jq -r '.items[] | select(.external_asset_id=="AMR-07") | .id' | head -n1)
DOOR_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/assets" | jq -r '.items[] | select(.external_asset_id=="DOOR-04") | .id' | head -n1)
curl -fsS -X POST "$API/api/v1/systems" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"site_id\":\"$SITE_ID\",\"name\":\"Synthetic Fleet System\",\"system_type\":\"fleet_manager\",\"external_system_id\":\"FLEET-01\",\"aliases\":[\"Test fleet\"]}" | jq
curl -fsS -X PATCH "$API/api/v1/assets/$ROBOT_ID/aliases?alias=Robot-7" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" | jq '.aliases'
curl -fsS -X POST "$API/api/v1/asset-dependencies" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"source_asset_id\":\"$ROBOT_ID\",\"target_asset_id\":\"$DOOR_ID\",\"dependency_type\":\"depends_on\"}" | jq
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/assets/$ROBOT_ID/dependencies" | jq
```

Expected result: `Robot-7` is retained as an alias and the robot-to-door dependency is returned. Run this block once per database reset to avoid duplicate synthetic records.

## Stage 6 — incident and evidence-backed timeline

Open **Incidents** and create:

| Field | Value |
|---|---|
| Engagement | Door and Wi-Fi ambiguity |
| Site | Berlin Test Lab |
| Title | AMR-07 delayed at Door 04 |
| Start | Local equivalent of 2026-04-07 09:12 UTC |
| Recovered | Local equivalent of 2026-04-07 09:14 UTC |
| Business impact | One mission delayed; synthetic exercise |

`datetime-local` uses the browser/computer timezone and this form accepts minute precision. In Berlin on this date (CEST, UTC+2), enter `11:12` and `11:14`; do not enter `09:12` unless the computer itself is set to UTC. The API patch below sets the evidence-derived second-precision boundaries.

The console form deliberately captures only the basic incident fields. Patch its executive summary and severity through the API before report testing:

```bash
export API='http://127.0.0.1:8000'
export ADMIN_HEADER='X-Role: admin'
export ACTOR_HEADER='X-Actor: stage-admin'
ENGAGEMENT_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/diagnostic-engagements" | jq -r '.items[] | select(.title=="Door and Wi-Fi ambiguity") | .id' | head -n1)
INCIDENT_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents" | jq -r '.items[] | select(.title=="AMR-07 delayed at Door 04") | .id' | head -n1)
curl -fsS -X PATCH "$API/api/v1/incidents/$INCIDENT_ID" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d '{"description":"Synthetic AMR-07 mission delay reconstructed across robot, fleet, door, and Wi-Fi exports.","severity":"high","started_at":"2026-04-07T09:12:58Z","recovered_at":"2026-04-07T09:13:24Z"}' | jq '{id, description, severity, started_at, recovered_at}'
```

Refresh **Incidents**, click **Investigate**, and test the **timeline** tab:

1. Search for `DOOR` and apply filters; then filter by `warning`.
2. Select an event and confirm its normalized fields, source, uncertainty, raw-record provenance, and original evidence link are visible.
3. Add annotation at the browser-local equivalent of `2026-04-07 09:13 UTC` titled `Operator observed pause`.
4. Save minute-precision boundaries using the browser-local equivalents of `09:12 UTC` to `09:14 UTC`, with reason `Reviewed against all three synthetic sources`.
5. Select the infrastructure source, apply offset `-3400` ms, and use reason `Fixture manifest supplies a 3400 ms source drift`. Confirm the timeline recalculates rather than rewriting raw evidence.
6. Export the timeline CSV and inspect that source/provenance columns are present.

Expected result: events remain chronological, annotation is distinct from source events, uncertainty remains explicit, and original raw evidence is unchanged.

Checkpoint:

```bash
python -m pytest tests/browser/test_timeline_editing.py tests/unit/test_incident_timing.py tests/performance/test_large_timeline.py -q
```

## Stage 7 — downtime, recovery, lifecycle, grouping, and metrics

In the incident workspace, open **downtime**:

- add a `blocked_robot` segment using the browser-local equivalents of `09:13 UTC` to `09:14 UTC`;
- set affected asset IDs to the Robot 07 UUID shown in the asset/API record, not `AMR-07`;
- set impact to `AMR-07 could not complete the mission`; and
- mark it analyst approved.

Add a recovery action at the browser-local equivalent of `09:13 UTC`, action type `operator_retry`, performed by `Synthetic operator`, affected asset Robot 07, outcome `Mission resumed after retry`.

Open **metrics** and add:

- lifecycle marker `occurred_at` at the local equivalent of `09:12 UTC`, source `Infrastructure export`, confidence `0.8`;
- lifecycle marker `technical_recovery_at` at the local equivalent of `09:13 UTC`, source `Fleet MISSION_RESUMED`, confidence `1.0`;
- recovery milestone `business_process_recovery` at the local equivalent of `09:14 UTC`, source `Robot navigation resumed`;
- event group `Door interaction sequence`, type `door_interaction`, using two or more canonical event UUIDs copied from the timeline, with an analyst note.

Expected result: lifecycle durations are calculated with their marker basis, technical and business recovery remain distinct, event grouping does not hide raw events, and dependency/recurrence panels state their methods and limitations.

Checkpoint:

```bash
python -m pytest tests/integration/test_incident_metrics_api.py tests/property/test_domain_properties.py -q
```

## Stage 8 — hypotheses, evidence, quality, and human review

Open **hypotheses** and create two hypotheses:

| Role | Title | Domain | Description |
|---|---|---|---|
| Primary | Door response delayed during Wi-Fi roam | network/Wi-Fi | Timing supports correlation, not proven causation |
| Alternative | Door controller independently delayed | door/lift/conveyor | Missing WCS/network trace prevents exclusion |

Attach at least one supporting raw record to the primary hypothesis and one `missing_expected` item with a blank raw-record ID. Use distinct evidence-origin groups where evidence comes from different systems. Add contextual or contradicting evidence to verify the count and confidence derivation update.

Open **quality** and click **Recalculate from underlying records**. Expected result: a score, grade, source coverage, issues, and confidence limitations are shown. Missing expected evidence must reduce certainty rather than disappear.

Approval and contradiction resolution are reviewer-only API actions and are exercised by:

```bash
python -m pytest \
  tests/browser/test_hypothesis_evidence.py \
  tests/integration/test_hypothesis_review_api.py \
  tests/unit/test_evidence_methodology.py \
  -q
```

The tests must show that an unresolved material contradiction blocks approval and that reviewer decisions are retained separately from computed confidence. Corrective-action records are covered in the end-to-end checkpoint in Stage 15.

With `$INCIDENT_ID` populated in Stage 6, run the API-only review and action checks:

```bash
HYPOTHESIS_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/hypotheses" | jq -r '.items[0].id')
EVIDENCE_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/evidence" | jq -r '([.items[] | select(.relation=="contradicts")][0] // .items[0]).id')
curl -fsS -X POST "$API/api/v1/evidence/$EVIDENCE_ID/review" \
  -H 'X-Role: reviewer' -H 'X-Actor: stage-reviewer' -H 'Content-Type: application/json' \
  -d '{"review_status":"reviewed","contradiction_resolution":"Reviewed against the synthetic source record"}' | jq
curl -fsS -X POST "$API/api/v1/hypotheses/$HYPOTHESIS_ID/reviews" \
  -H 'X-Role: reviewer' -H 'X-Actor: stage-reviewer' -H 'Content-Type: application/json' \
  -d '{"decision":"accept","reviewer_confidence":0.7,"note":"Accepted for synthetic workflow testing"}' | jq
curl -fsS -X POST "$API/api/v1/incidents/$INCIDENT_ID/corrective-actions" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d '{"description":"Collect a synchronized WCS/network trace for recurrence","owner":"Synthetic site lead","status":"proposed"}' | jq
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/corrective-actions" | jq
```

Expected result: computed analyst confidence remains traceable, reviewer judgment is stored separately, and the corrective action has an owner and status.

## Stage 9 — reports, redaction, approval, comparison, and vendor package

First capture IDs used by API checks. In **Terminal B**:

```bash
export API='http://127.0.0.1:8000'
export ADMIN_HEADER='X-Role: admin'
export ACTOR_HEADER='X-Actor: stage-admin'
ENGAGEMENT_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/diagnostic-engagements" | jq -r '.items[] | select(.title=="Door and Wi-Fi ambiguity") | .id' | head -n1)
INCIDENT_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents" | jq -r '.items[] | select(.title=="AMR-07 delayed at Door 04") | .id' | head -n1)
RAW_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/timeline" | jq -r '.items[] | select(.raw_record_id != null) | .raw_record_id' | head -n1)
printf 'ENGAGEMENT_ID=%s\nINCIDENT_ID=%s\nRAW_ID=%s\n' "$ENGAGEMENT_ID" "$INCIDENT_ID" "$RAW_ID"
```

All three values must be non-empty. In the browser console (Developer Tools → Console), temporarily enable the local admin role:

```javascript
localStorage.rfiiRole = 'admin'; location.reload();
```

This header-based role switch works only because local authentication is disabled. It is not a production sign-in mechanism.

Open the incident and **reports**:

1. Generate an executive report with email, IPv4, and MAC redaction checked.
2. Generate a technical report and include the `$RAW_ID` value.
3. Generate a vendor-support report.
4. Approve a version with note `Synthetic workflow reviewed`; the approved version becomes immutable.
5. Build a vendor package with only `$RAW_ID` selected.
6. Download JSON/Markdown/HTML/PDF/CSV artifacts and the vendor ZIP; confirm the ZIP contains only explicitly selected evidence and report files.

Generate one more version after adding an annotation, then compare versions through the API:

```bash
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" \
  "$API/api/v1/incidents/$INCIDENT_ID/reports/compare?left=1&right=2" | jq
```

Expected result: changed sections, evidence/confidence/metric change flags, and approval history are explicit.

Exercise redaction preview independently of report generation:

```bash
curl -fsS -X POST "$API/api/v1/incidents/$INCIDENT_ID/redaction-preview" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d '{"snapshot":{"contact":"operator@example.test","ip":"10.12.0.7","mac":"aa:bb:cc:dd:ee:ff"},"rules":{"emails":true,"ipv4":true,"mac":true}}' | jq
```

Expected result: all three values are masked, replacement counts are non-zero, and an audit ID is returned.

Checkpoint:

```bash
python -m pytest \
  tests/browser/test_report_approval.py \
  tests/browser/test_vendor_package.py \
  tests/unit/test_buyer_reports.py \
  -q
```

If report approval is blocked, read the returned blockers: approve/review the hypotheses, resolve material contradictions, or explicitly justify why no alternative exists. Do not bypass those gates.

## Stage 10 — authentication, roles, tenant isolation, audit, and limits

Stop Terminal A with `Ctrl-C`. In Terminal B, keep the Stage 0 variables but enable authentication and create the first administrator:

```bash
export RFII_AUTH_REQUIRED='true'
python tools/bootstrap_admin.py admin@example.test
```

Enter a unique password of at least 12 characters when prompted. Restart Terminal A after exporting the same settings with `RFII_AUTH_REQUIRED=true`:

```bash
uvicorn apps.diagnostic_api.main:app --reload --host 127.0.0.1 --port 8000
```

Browser checks:

1. Open **Sign in**, use the administrator credentials, and confirm **Admin** appears.
2. Create one user for each role you want to inspect: analyst, reviewer, operator, partner, and viewer.
3. Sign in as viewer: forms requiring write/upload/approve must be hidden.
4. Sign in as analyst: write and upload work, approval and Admin remain hidden.
5. Sign in as reviewer: approval is available, mutation forms remain hidden.
6. Sign back in as administrator and inspect the audit API with a bearer token from the login response if desired.

To explicitly test password reset, token invalidation, and account disable, create a disposable viewer from **Admin**, then use the development-only reset token returned by `/auth/password-reset/request`. The automated authentication test below performs this without exposing a password in shell history. Confirm that the old password/token stops working after reset and that login stops working after the administrator disables the account. Production never returns reset tokens in the API response.

Automated security checkpoint:

```bash
python -m pytest \
  tests/browser/test_login.py \
  tests/browser/test_role_permissions.py \
  tests/security/test_authentication.py \
  tests/security/test_tenant_scope.py \
  tests/security/test_rate_limit_metrics.py \
  tests/security/test_evidence_encryption.py \
  tests/security/test_upload_security.py \
  -q
```

After returning to unauthenticated local mode as described below, confirm the audit stream contains actions from this run:

```bash
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/audit?limit=20" \
  | jq '.items[] | {action, actor, entity_type, entity_id}'
```

Expected result: authentication is required, role permissions and customer scope are enforced server-side, rate-limit events are measurable, evidence encryption round-trips, and unsafe uploads are rejected.

For Stages 11–12, either use bearer tokens or return to local test mode: stop the API, export `RFII_AUTH_REQUIRED=false` in both terminals, restart it, and restore the local admin role in the browser.

## Stage 11 — private dataset enablement, reuse measurement, and validation evidence

This registry stores metadata and private-workspace references, not dataset contents. In Terminal B, ensure `$ENGAGEMENT_ID` is still populated, then run:

```bash
DATASET_JSON=$(curl -fsS -X POST "$API/api/v1/datasets" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"dataset_id\":\"synthetic-door-wifi-001\",\"engagement_id\":\"$ENGAGEMENT_ID\",\"file_count\":3,\"source_categories\":[\"robot\",\"fleet\",\"infrastructure\"],\"hashes\":[\"synthetic-hash-1\",\"synthetic-hash-2\",\"synthetic-hash-3\"],\"time_range\":{\"start\":\"2026-04-07T09:12:58Z\",\"end\":\"2026-04-07T09:15:00Z\"},\"customer_pseudonym\":\"customer-synthetic-001\",\"access_list\":[\"stage-tester\"],\"private_workspace_reference\":\"private://synthetic-workspace/door-wifi-001\"}")
echo "$DATASET_JSON" | jq
DATASET_REGISTRATION_ID=$(echo "$DATASET_JSON" | jq -r '.id')
curl -fsS -X POST "$API/api/v1/datasets/$DATASET_REGISTRATION_ID/import-effort" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d '{"source_category":"robot","mapping_minutes":12,"code_change_minutes":0,"manual_cleanup_minutes":3,"unknown_fields":["vendor_substate"],"reusable_percentage":90,"blocked_fields":[],"analyst_minutes":15,"developer_minutes":0,"note":"Synthetic workflow measurement"}' | jq
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/datasets" | jq '{contents_exposed, count:(.items|length)}'
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/datasets/$DATASET_REGISTRATION_ID/import-effort" | jq
```

Expected result: `contents_exposed` is `false`; effort totals and reusable percentage are calculated.

In the browser, open **Validation**, add a record titled `Synthetic workflow rehearsal`, reference `fixtures/incident_001_door_wifi/manifest.yaml`, and check **Synthetic evidence**. Expected result: it saves but cannot satisfy a real commercial gate.

Checkpoint:

```bash
python -m pytest \
  tests/integration/test_dataset_enablement.py \
  tests/unit/test_anonymisation.py \
  tests/unit/test_commercial_tools.py \
  tests/security/test_private_data_guard.py \
  -q
```

### Durable jobs, non-causal suggestions, incident comparison, and validation decisions

These service features have API surfaces rather than dedicated console forms. Run them before deleting the engagement:

```bash
JOB_KEY="manual-ingest-check-$(date +%s)"
JOB_JSON=$(curl -fsS -X POST "$API/api/v1/jobs" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"job_type\":\"ingest\",\"idempotency_key\":\"$JOB_KEY\",\"payload\":{\"purpose\":\"manual test\"},\"max_retries\":3}")
echo "$JOB_JSON" | jq
JOB_ID=$(echo "$JOB_JSON" | jq -r '.id')
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/jobs/$JOB_ID" | jq
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/admin/jobs/$JOB_ID" | jq
curl -fsS -X POST "$API/api/v1/diagnostic-engagements/$ENGAGEMENT_ID/incident-suggestions" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' -d '{}' | jq
```

Expected result: public job status omits internal error detail, admin status includes attempt diagnostics, and incident suggestions declare `noncausal: true`. The local worker is not running, so a queued job remaining queued is expected; Stage 13 verifies worker processing.

Create a second synthetic incident for recurrence comparison:

```bash
SECOND_JSON=$(curl -fsS -X POST "$API/api/v1/incidents" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"diagnostic_engagement_id\":\"$ENGAGEMENT_ID\",\"site_id\":\"$SITE_ID\",\"title\":\"AMR-07 repeat door delay\",\"description\":\"Synthetic comparison case\",\"started_at\":\"2026-04-08T09:13:00Z\",\"recovered_at\":\"2026-04-08T09:13:30Z\",\"business_impact\":\"Synthetic repeat\",\"severity\":\"high\"}")
echo "$SECOND_JSON" | jq
SECOND_INCIDENT_ID=$(echo "$SECOND_JSON" | jq -r '.id')
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/compare/$SECOND_INCIDENT_ID" | jq
curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/incidents/$INCIDENT_ID/recurring-matches" | jq
```

Expected result: comparison explains shared/different attributes and recurring matches identify their transparent method rather than claiming causal similarity.

Capture the synthetic validation record created in the browser and record a synthetic-only decision:

```bash
VALIDATION_ID=$(curl -fsS -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" "$API/api/v1/validation-records" | jq -r '.items[] | select(.title=="Synthetic workflow rehearsal") | .id' | head -n1)
curl -fsS -X POST "$API/api/v1/validation-decisions" \
  -H "$ADMIN_HEADER" -H "$ACTOR_HEADER" -H 'Content-Type: application/json' \
  -d "{\"decision\":\"pivot\",\"rationale\":\"Synthetic rehearsal cannot close a commercial gate\",\"validation_record_ids\":[\"$VALIDATION_ID\"]}" | jq
```

Expected result: the evidence ID is linked to the decision, while the documented policy continues to state that synthetic records never satisfy commercial gates.

## Stage 12 — retention and independently approved deletion

**Destructive stage:** deletion execution cannot be undone. Use the synthetic engagement created in this guide only. Skip manual execution if you want to retain it for later exploration; the automated retention test still validates the feature safely.

The request creator and approver must be different actors:

```bash
DELETE_JSON=$(curl -fsS -X POST "$API/api/v1/diagnostic-engagements/$ENGAGEMENT_ID/deletion-preview" \
  -H 'X-Role: admin' -H 'X-Actor: deletion-requester' -H 'Content-Type: application/json' \
  -d '{"reason":"End of synthetic manual workflow test"}')
echo "$DELETE_JSON" | jq
DELETE_REQUEST_ID=$(echo "$DELETE_JSON" | jq -r '.id')
curl -fsS -X POST "$API/api/v1/deletion-requests/$DELETE_REQUEST_ID/approve" \
  -H 'X-Role: reviewer' -H 'X-Actor: independent-reviewer' -H 'Content-Type: application/json' \
  -d '{}' | jq
```

Review the preview counts before execution. Only if the ID and scope are correct:

```bash
curl -fsS -X POST "$API/api/v1/deletion-requests/$DELETE_REQUEST_ID/execute" \
  -H 'X-Role: admin' -H 'X-Actor: deletion-executor' -H 'Content-Type: application/json' \
  -d '{}' | jq
```

Expected result: the engagement's database records and stored evidence are removed, while the deletion/audit record remains. Verify same-actor approval is rejected through the automated test:

```bash
python -m pytest tests/security/test_retention.py -q
```

If you executed deletion, Stages 3–9 can be repeated to prove a clean second run.

## Stage 13 — PostgreSQL, durable worker, and Docker deployment

Stop the local server first so port 8000 is free. Create `.env` from the example if it does not exist and set unique secrets. Do not commit `.env`.

```bash
cp -n .env.example .env
python -c 'import secrets; print("POSTGRES_PASSWORD=" + secrets.token_urlsafe(32)); print("RFII_SECRET_KEY=" + secrets.token_urlsafe(48))'
```

Copy the two generated values into `.env`, replacing the example values. Then run:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api worker db
curl -fsS http://127.0.0.1:8000/health | jq
```

Expected result: database, API, and worker are running; database and API become healthy; the worker polls durable jobs without crashing.

Create the first Docker administrator:

```bash
docker compose exec api python tools/bootstrap_admin.py docker-admin@example.test
```

Open <http://127.0.0.1:8000/>, sign in, and repeat the small path: create engagement → register source → preview → preserve → commit → create incident → investigate. This proves the PostgreSQL deployment behaves like local SQLite.

Checkpoint:

```bash
python -m pytest tests/migration/test_migrations.py tests/postgres/test_postgres_semantics.py -q
docker compose ps
```

The PostgreSQL test may skip unless its documented test database variable is available; the live Compose smoke path above is still required.

## Stage 14 — backup/restore, reliability, security, and release gates

### Backup

With Compose running and `.env` loaded as expected by the scripts:

```bash
./deployment/on_prem/backup.sh
find backups -maxdepth 2 -type f -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort
```

Expected result: database and evidence backup artifacts plus integrity metadata are created. If backup encryption is configured, confirm no plaintext final backup remains.

### Restore rehearsal

Restore overwrites deployment data. Perform it only against this disposable test stack, never a live environment. Read the script's usage and validate its contract before supplying an artifact:

```bash
./deployment/on_prem/restore.sh --help || true
python -m pytest tests/backup_restore/test_backup_restore_contract.py -q
```

Resolve and inspect the newest backup directory, then pass that exact path to restore:

```bash
BACKUP_DIR=$(find backups -mindepth 1 -maxdepth 1 -type d | sort | tail -n1)
printf 'Restore candidate: %s\n' "$BACKUP_DIR"
find "$BACKUP_DIR" -maxdepth 1 -type f -printf '%f\n' | sort
./deployment/on_prem/restore.sh "$BACKUP_DIR"
```

Type `RESTORE` only after confirming the candidate contains `SHA256SUMS`, a database artifact, and an evidence artifact from this disposable stack. Then confirm `/health` and one preserved report/evidence hash. Record the artifact name, start/end time, result, and recovery-time objective in your test notes.

### Reliability, migration, and security gates

```bash
python -m pytest \
  tests/fault \
  tests/performance \
  tests/migration \
  tests/security \
  tests/backup_restore \
  -q
python scripts/validate_scorecard.py
python scripts/release_gate.py
POSTGRES_PASSWORD='compose-check-only' \
RFII_SECRET_KEY='compose-check-secret-at-least-32-characters' \
docker compose config --quiet
```

Expected result: fault injection, large timeline, migrations, security, retention, backup contracts, scorecard evidence, release claims, and Compose configuration all pass.

TLS is configuration-dependent. For a real on-prem host, follow `deployment/on_prem/secure_install.md`, install a trusted certificate, use the secure Compose overlay described there, and verify HTTPS plus certificate hostname/expiry. Do not claim TLS tested from the plain localhost stack.

## Stage 15 — full regression and final evidence

Stop Compose if you no longer need it:

```bash
docker compose down
```

This keeps named database/evidence volumes. `docker compose down -v` permanently deletes those volumes and should be used only when you explicitly want to erase the disposable Docker data.

Reapply the Stage 0 virtual environment and run the full suite:

```bash
source .venv/bin/activate
python -m pytest -q
```

Expected result: the complete collected suite passes, with only environment-specific tests explicitly skipped. It includes all browser journeys and the full diagnostic workflow:

```bash
python -m pytest tests/end_to_end/test_diagnostic_workflow.py tests/browser -q
```

Save auditable evidence without modifying product documentation:

```bash
mkdir -p storage/manual-test/test-evidence
python -m pytest -q --junitxml=storage/manual-test/test-evidence/pytest.xml
git status --short > storage/manual-test/test-evidence/git-status.txt
git rev-parse HEAD > storage/manual-test/test-evidence/commit.txt
date --iso-8601=seconds > storage/manual-test/test-evidence/completed-at.txt
```

Use this final acceptance record:

```text
Commit tested:
Tester:
Environment (OS/Python/Docker/browser):
Stages passed:
Stages skipped and reason:
Failed checks / issue links:
Synthetic fixture used:
Full pytest result:
Docker/PostgreSQL result:
Backup/restore result:
TLS result (or not tested):
Testing completed at:
```

Passing synthetic tests means the implementation works against its specified fixtures and contracts. It does not close the real-operator, real-dataset, security-review, or commercial-validation gates documented in `next.md`.

## Stage 16 — optional preserved ROS 2 autonomy demo

This stage is unrelated to the active product runtime. Run it only on a machine with ROS 2 Jazzy and the required Gazebo/Nav2 dependencies.

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-clean-cache \
  --packages-select factory_inspection_interfaces factory_inspection_mission
../tools/run_iteration_smoke_test.sh
```

For the visual legacy stack:

```bash
cd /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/legacy/autonomy_demo
./tools/run_live_demo_stack.sh
```

Expected result and troubleshooting are documented in `legacy/autonomy_demo/docs/ITERATION_TESTING_README.md`. Do not interpret this simulated robotics run as customer validation of the incident-intelligence product.

## Reset and troubleshooting

### Reset only the local manual workflow

Stop the local API. The following files are disposable test state, but removal is irreversible. Verify the exact paths before deleting them:

```bash
ls -ld \
  /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/storage/manual-test.db \
  /home/samarth/projects/industrial-robot-operations-intelligence/incident-intelligence/storage/manual-test
```

After verification, remove those two exact targets manually and rerun Stage 0 migrations. Do not delete the whole `storage/` directory because it may contain other work.

### Common failures

| Symptom | Check |
|---|---|
| Port 8000 already in use | Stop the earlier Uvicorn/Compose process, or use `--port 8001` and update `$API`. |
| UI lists no engagement/source | Confirm the selected engagement and that both terminals use the same `RFII_DATABASE_URL`. |
| `401` after enabling auth | Sign in for a bearer token; header roles are intentionally ignored in authenticated mode. |
| Report approval returns `409` | Read quality blockers; review contradictions and hypotheses instead of bypassing them. |
| Playwright cannot launch | Run `python -m playwright install chromium` and install its reported OS libraries. |
| Docker API unhealthy | Inspect `docker compose logs api db`; most first-run failures are mismatched `.env` credentials or port conflicts. |
| Migration mismatch | Run `python -m alembic current` and `python -m alembic heads`; both should identify the current head after upgrade. |
| ZIP rejected | Read the structured rejection reason; nested/encrypted/linked/oversized archives are rejected by design. |
| Fixture times appear shifted | Keep the site/source timezone at UTC; clock drift belongs in the explicit offset field. |

## Feature-to-test index

| Capability | Manual stage | Primary automated evidence |
|---|---:|---|
| Product scope and read-only boundary | 2 | `tests/contract/test_product_scope.py` |
| CSV/JSON/JSONL/structured parsing and mapping | 4 | `tests/unit/test_ingestion.py`, `tests/integration/test_ingestion_profiles.py` |
| Streaming, encodings, ZIP and upload security | 4 | `tests/unit/test_ingestion_hardening.py`, `tests/security/test_upload_security.py` |
| Immutable evidence, hashes, provenance, idempotency | 4, 6 | `tests/contract/test_critical_invariants.py`, `tests/end_to_end/test_diagnostic_workflow.py` |
| Registry, aliases, dependencies and connector contracts | 5, 7 | `tests/contract/test_connectors.py`, `tests/connector_contract/` |
| Clock alignment, uncertainty, downtime and recovery | 6, 7 | `tests/unit/test_incident_timing.py`, `tests/integration/test_incident_metrics_api.py` |
| Hypothesis confidence, alternatives and review | 8 | `tests/unit/test_evidence_methodology.py`, `tests/integration/test_hypothesis_review_api.py` |
| Data quality and corrective actions | 8 | `tests/end_to_end/test_diagnostic_workflow.py` |
| Buyer reports, PDF, redaction and vendor package | 9 | `tests/unit/test_buyer_reports.py`, browser report tests |
| Authentication, RBAC, tenant scope and audit | 10 | `tests/security/`, browser login/role tests |
| Private dataset metadata and anonymisation | 11 | `tests/integration/test_dataset_enablement.py`, `tests/unit/test_anonymisation.py` |
| Validation and commercial tools | 11 | `tests/unit/test_commercial_tools.py` |
| Retention and independent deletion approval | 12 | `tests/security/test_retention.py` |
| PostgreSQL, migrations and worker deployment | 13 | `tests/postgres/`, `tests/migration/` |
| Fault, load, backup and release readiness | 14, 15 | `tests/fault/`, `tests/performance/`, `tests/backup_restore/`, `tests/release/` |
