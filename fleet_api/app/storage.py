from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


FINDING_STATUSES = {
    "OPEN",
    "ACKNOWLEDGED",
    "ASSIGNED",
    "REINSPECTION_REQUESTED",
    "RESOLVED",
    "CLOSED",
    "REJECTED",
}

MISSION_STATUSES = {
    "QUEUED",
    "ACTIVE",
    "PAUSED",
    "CANCELLED",
    "COMPLETED",
    "FAILED",
    "REJECTED",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_scoped_id(tenant_id: str, natural_id: str) -> str:
    return f"{tenant_id}:{natural_id}"


def _json_dump(value: Any) -> str:
    if value is None:
        value = {}
    return json.dumps(value, sort_keys=True)


def _json_load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


@dataclass
class FleetWatchStore:
    db_path: Path

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    hashed_password TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    company TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tenant_robots (
                    tenant_id TEXT NOT NULL,
                    robot_id TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, robot_id)
                );

                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    map_id TEXT NOT NULL,
                    coordinate_frame TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_sites_tenant_site
                    ON sites (tenant_id, site_id);

                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    criticality TEXT NOT NULL,
                    owner_team TEXT NOT NULL,
                    inspection_profile_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    enabled_modalities_json TEXT NOT NULL,
                    checkpoint_name TEXT NOT NULL,
                    viewpoint_id TEXT NOT NULL,
                    position_tolerance_m REAL NOT NULL,
                    orientation_tolerance_rad REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    latest_label TEXT,
                    latest_severity TEXT,
                    latest_health_score REAL,
                    latest_confidence REAL,
                    latest_image_path TEXT,
                    latest_annotated_image_path TEXT,
                    outstanding INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_tenant_asset
                    ON assets (tenant_id, asset_id);

                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    run_id TEXT,
                    scenario_id TEXT,
                    round_number INTEGER,
                    mission_profile TEXT,
                    mission_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    mission_decision TEXT,
                    decision_reason TEXT,
                    priority TEXT NOT NULL,
                    selected_assets_json TEXT NOT NULL,
                    follow_up_assets_json TEXT NOT NULL,
                    linked_finding_id TEXT,
                    requested_by TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_missions_tenant_mission
                    ON missions (tenant_id, mission_id);

                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    mission_id TEXT,
                    checkpoint_name TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    image_path TEXT,
                    raw_image_path TEXT,
                    annotated_image_path TEXT,
                    media_type TEXT NOT NULL,
                    timestamp_ns INTEGER,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_tenant_evidence
                    ON evidence (tenant_id, evidence_id);

                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    mission_id TEXT,
                    evidence_id TEXT,
                    schema_version TEXT NOT NULL,
                    source_round_number INTEGER,
                    checkpoint_name TEXT NOT NULL,
                    label TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    review_required INTEGER NOT NULL DEFAULT 0,
                    recommended_action TEXT,
                    health_score REAL,
                    confidence REAL,
                    outstanding INTEGER NOT NULL DEFAULT 1,
                    assigned_to TEXT,
                    acknowledged_by TEXT,
                    resolved_by TEXT,
                    resolution_note TEXT,
                    detected_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_findings_tenant_finding
                    ON findings (tenant_id, finding_id);

                CREATE TABLE IF NOT EXISTS finding_events (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    note TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_finding_events_tenant_finding
                    ON finding_events (tenant_id, finding_id, created_at);

                CREATE TABLE IF NOT EXISTS sync_runs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sync_runs_tenant_created
                    ON sync_runs (tenant_id, created_at DESC);
                """
            )

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT email, hashed_password, tenant_id, company FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def create_user(
        self,
        *,
        email: str,
        hashed_password: str,
        tenant_id: str,
        company: str,
        robots: list[str],
    ) -> dict[str, Any]:
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (email, hashed_password, tenant_id, company, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, hashed_password, tenant_id, company, now, now),
            )
            self._replace_tenant_robots(conn, tenant_id, robots)
        return {
            "email": email,
            "tenant_id": tenant_id,
            "company": company,
        }

    def ensure_user(
        self,
        *,
        email: str,
        hashed_password: str,
        tenant_id: str,
        company: str,
        robots: list[str],
    ) -> dict[str, Any]:
        existing = self.get_user_by_email(email)
        if existing is not None:
            with self.connect() as conn:
                self._replace_tenant_robots(conn, tenant_id, robots)
            return existing
        return self.create_user(
            email=email,
            hashed_password=hashed_password,
            tenant_id=tenant_id,
            company=company,
            robots=robots,
        )

    def list_tenant_robots(self, tenant_id: str) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT robot_id FROM tenant_robots WHERE tenant_id = ? ORDER BY robot_id",
                (tenant_id,),
            ).fetchall()
        return [row["robot_id"] for row in rows]

    def _replace_tenant_robots(
        self,
        conn: sqlite3.Connection,
        tenant_id: str,
        robots: list[str],
    ) -> None:
        unique_robots = sorted(dict.fromkeys(robots))
        conn.execute("DELETE FROM tenant_robots WHERE tenant_id = ?", (tenant_id,))
        conn.executemany(
            "INSERT INTO tenant_robots (tenant_id, robot_id) VALUES (?, ?)",
            [(tenant_id, robot_id) for robot_id in unique_robots],
        )

    def upsert_site(self, tenant_id: str, site: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        site_id = str(site["site_id"])
        scoped_id = make_scoped_id(tenant_id, site_id)
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM sites WHERE id = ?",
                (scoped_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO sites (
                    id, tenant_id, site_id, schema_version, name, timezone, map_id,
                    coordinate_frame, status, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    name = excluded.name,
                    timezone = excluded.timezone,
                    map_id = excluded.map_id,
                    coordinate_frame = excluded.coordinate_frame,
                    status = excluded.status,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    scoped_id,
                    tenant_id,
                    site_id,
                    str(site.get("schema_version", "site.v1")),
                    str(site.get("name", site_id)),
                    str(site.get("timezone", "UTC")),
                    str(site.get("map_id", "")),
                    str(site.get("coordinate_frame", "map")),
                    str(site.get("status", "ACTIVE")),
                    _json_dump(site.get("metadata", {})),
                    created_at,
                    now,
                ),
            )
        return self.get_site(tenant_id, site_id)

    def list_sites(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT site_id, schema_version, name, timezone, map_id, coordinate_frame,
                       status, metadata_json, created_at, updated_at
                FROM sites
                WHERE tenant_id = ?
                ORDER BY name
                """,
                (tenant_id,),
            ).fetchall()
        return [self._site_row_to_dict(row) for row in rows]

    def get_site(self, tenant_id: str, site_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT site_id, schema_version, name, timezone, map_id, coordinate_frame,
                       status, metadata_json, created_at, updated_at
                FROM sites
                WHERE tenant_id = ? AND site_id = ?
                """,
                (tenant_id, site_id),
            ).fetchone()
        if row is None:
            return None
        return self._site_row_to_dict(row)

    def _site_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = _json_load(data.pop("metadata_json", "{}"), {})
        return data

    def upsert_asset(
        self,
        tenant_id: str,
        site_id: str,
        asset: dict[str, Any],
    ) -> dict[str, Any]:
        now = utc_now_iso()
        asset_id = str(asset["asset_id"])
        scoped_id = make_scoped_id(tenant_id, asset_id)
        checkpoint = asset.get("checkpoint", {})
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM assets WHERE id = ?",
                (scoped_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO assets (
                    id, tenant_id, asset_id, site_id, schema_version, name, asset_type, zone,
                    priority, criticality, owner_team, inspection_profile_id, status, tags_json,
                    enabled_modalities_json, checkpoint_name, viewpoint_id, position_tolerance_m,
                    orientation_tolerance_rad, metadata_json, latest_label, latest_severity,
                    latest_health_score, latest_confidence, latest_image_path,
                    latest_annotated_image_path, outstanding, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    site_id = excluded.site_id,
                    schema_version = excluded.schema_version,
                    name = excluded.name,
                    asset_type = excluded.asset_type,
                    zone = excluded.zone,
                    priority = excluded.priority,
                    criticality = excluded.criticality,
                    owner_team = excluded.owner_team,
                    inspection_profile_id = excluded.inspection_profile_id,
                    status = excluded.status,
                    tags_json = excluded.tags_json,
                    enabled_modalities_json = excluded.enabled_modalities_json,
                    checkpoint_name = excluded.checkpoint_name,
                    viewpoint_id = excluded.viewpoint_id,
                    position_tolerance_m = excluded.position_tolerance_m,
                    orientation_tolerance_rad = excluded.orientation_tolerance_rad,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    scoped_id,
                    tenant_id,
                    asset_id,
                    site_id,
                    str(asset.get("schema_version", "asset_registry.v1")),
                    str(asset.get("name", asset_id)),
                    str(asset.get("asset_type", "unknown_asset")),
                    str(asset.get("zone", "unassigned")),
                    int(asset.get("priority", 0)),
                    str(asset.get("criticality", "MEDIUM")),
                    str(asset.get("owner_team", "unassigned")),
                    str(asset.get("inspection_profile_id", "")),
                    str(asset.get("status", "ACTIVE")),
                    _json_dump(asset.get("tags", [])),
                    _json_dump(asset.get("enabled_modalities", [])),
                    str(checkpoint.get("name", asset.get("checkpoint_name", asset_id))),
                    str(checkpoint.get("viewpoint_id", asset.get("viewpoint_id", ""))),
                    float(checkpoint.get("position_tolerance_m", asset.get("position_tolerance_m", 0.0))),
                    float(checkpoint.get("orientation_tolerance_rad", asset.get("orientation_tolerance_rad", 0.0))),
                    _json_dump(
                        {
                            "checkpoint": checkpoint,
                            "source_asset_record": asset,
                        }
                    ),
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    created_at,
                    now,
                ),
            )
        return self.get_asset(tenant_id, asset_id)

    def update_asset_runtime_state(
        self,
        tenant_id: str,
        asset_id: str,
        *,
        latest_label: str | None,
        latest_severity: str | None,
        latest_health_score: float | None,
        latest_confidence: float | None,
        latest_image_path: str | None,
        latest_annotated_image_path: str | None,
        outstanding: bool,
    ) -> None:
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE assets
                SET latest_label = ?,
                    latest_severity = ?,
                    latest_health_score = ?,
                    latest_confidence = ?,
                    latest_image_path = ?,
                    latest_annotated_image_path = ?,
                    outstanding = ?,
                    updated_at = ?
                WHERE tenant_id = ? AND asset_id = ?
                """,
                (
                    latest_label,
                    latest_severity,
                    latest_health_score,
                    latest_confidence,
                    latest_image_path,
                    latest_annotated_image_path,
                    1 if outstanding else 0,
                    now,
                    tenant_id,
                    asset_id,
                ),
            )

    def list_assets(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT asset_id, site_id, schema_version, name, asset_type, zone, priority,
                       criticality, owner_team, inspection_profile_id, status, tags_json,
                       enabled_modalities_json, checkpoint_name, viewpoint_id,
                       position_tolerance_m, orientation_tolerance_rad, metadata_json,
                       latest_label, latest_severity, latest_health_score, latest_confidence,
                       latest_image_path, latest_annotated_image_path, outstanding,
                       created_at, updated_at
                FROM assets
                WHERE tenant_id = ?
                ORDER BY
                    CASE criticality
                        WHEN 'CRITICAL' THEN 0
                        WHEN 'HIGH' THEN 1
                        WHEN 'MEDIUM' THEN 2
                        ELSE 3
                    END,
                    priority DESC,
                    name
                """,
                (tenant_id,),
            ).fetchall()
        return [self._asset_row_to_dict(row) for row in rows]

    def get_asset(self, tenant_id: str, asset_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT asset_id, site_id, schema_version, name, asset_type, zone, priority,
                       criticality, owner_team, inspection_profile_id, status, tags_json,
                       enabled_modalities_json, checkpoint_name, viewpoint_id,
                       position_tolerance_m, orientation_tolerance_rad, metadata_json,
                       latest_label, latest_severity, latest_health_score, latest_confidence,
                       latest_image_path, latest_annotated_image_path, outstanding,
                       created_at, updated_at
                FROM assets
                WHERE tenant_id = ? AND asset_id = ?
                """,
                (tenant_id, asset_id),
            ).fetchone()
        if row is None:
            return None
        return self._asset_row_to_dict(row)

    def _asset_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        metadata = _json_load(data.pop("metadata_json", "{}"), {})
        data["tags"] = _json_load(data.pop("tags_json", "[]"), [])
        data["enabled_modalities"] = _json_load(data.pop("enabled_modalities_json", "[]"), [])
        data["metadata"] = metadata
        data["checkpoint"] = metadata.get("checkpoint", {})
        data["outstanding"] = bool(data.get("outstanding", 0))
        return data

    def upsert_mission(self, tenant_id: str, mission: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        mission_id = str(mission["mission_id"])
        scoped_id = make_scoped_id(tenant_id, mission_id)
        status_value = str(mission.get("status", "QUEUED")).upper()
        if status_value not in MISSION_STATUSES:
            status_value = "QUEUED"
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM missions WHERE id = ?",
                (scoped_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO missions (
                    id, tenant_id, mission_id, site_id, schema_version, run_id, scenario_id,
                    round_number, mission_profile, mission_type, status, mission_decision,
                    decision_reason, priority, selected_assets_json, follow_up_assets_json,
                    linked_finding_id, requested_by, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    site_id = excluded.site_id,
                    schema_version = excluded.schema_version,
                    run_id = excluded.run_id,
                    scenario_id = excluded.scenario_id,
                    round_number = excluded.round_number,
                    mission_profile = excluded.mission_profile,
                    mission_type = excluded.mission_type,
                    status = excluded.status,
                    mission_decision = excluded.mission_decision,
                    decision_reason = excluded.decision_reason,
                    priority = excluded.priority,
                    selected_assets_json = excluded.selected_assets_json,
                    follow_up_assets_json = excluded.follow_up_assets_json,
                    linked_finding_id = excluded.linked_finding_id,
                    requested_by = excluded.requested_by,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    scoped_id,
                    tenant_id,
                    mission_id,
                    str(mission.get("site_id", "factory_demo_site")),
                    str(mission.get("schema_version", "mission.v1")),
                    mission.get("run_id"),
                    mission.get("scenario_id"),
                    mission.get("round_number"),
                    mission.get("mission_profile"),
                    str(mission.get("mission_type", "manual")),
                    status_value,
                    mission.get("mission_decision"),
                    mission.get("decision_reason"),
                    str(mission.get("priority", "normal")),
                    _json_dump(mission.get("selected_assets", [])),
                    _json_dump(mission.get("follow_up_assets", [])),
                    mission.get("linked_finding_id"),
                    mission.get("requested_by"),
                    _json_dump(mission.get("metadata", {})),
                    created_at,
                    now,
                ),
            )
        return self.get_mission(tenant_id, mission_id)

    def list_missions(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT mission_id, site_id, schema_version, run_id, scenario_id, round_number,
                       mission_profile, mission_type, status, mission_decision, decision_reason,
                       priority, selected_assets_json, follow_up_assets_json, linked_finding_id,
                       requested_by, metadata_json, created_at, updated_at
                FROM missions
                WHERE tenant_id = ?
                ORDER BY
                    CASE status
                        WHEN 'QUEUED' THEN 0
                        WHEN 'ACTIVE' THEN 1
                        WHEN 'PAUSED' THEN 2
                        ELSE 3
                    END,
                    updated_at DESC
                """,
                (tenant_id,),
            ).fetchall()
        return [self._mission_row_to_dict(row) for row in rows]

    def get_mission(self, tenant_id: str, mission_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT mission_id, site_id, schema_version, run_id, scenario_id, round_number,
                       mission_profile, mission_type, status, mission_decision, decision_reason,
                       priority, selected_assets_json, follow_up_assets_json, linked_finding_id,
                       requested_by, metadata_json, created_at, updated_at
                FROM missions
                WHERE tenant_id = ? AND mission_id = ?
                """,
                (tenant_id, mission_id),
            ).fetchone()
        if row is None:
            return None
        return self._mission_row_to_dict(row)

    def update_mission_status(
        self,
        tenant_id: str,
        mission_id: str,
        status_value: str,
    ) -> dict[str, Any] | None:
        normalized_status = status_value.upper()
        if normalized_status not in MISSION_STATUSES:
            raise ValueError(f"Unsupported mission status: {status_value}")
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE missions
                SET status = ?, updated_at = ?
                WHERE tenant_id = ? AND mission_id = ?
                """,
                (normalized_status, now, tenant_id, mission_id),
            )
        return self.get_mission(tenant_id, mission_id)

    def _mission_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["selected_assets"] = _json_load(data.pop("selected_assets_json", "[]"), [])
        data["follow_up_assets"] = _json_load(data.pop("follow_up_assets_json", "[]"), [])
        data["metadata"] = _json_load(data.pop("metadata_json", "{}"), {})
        return data

    def upsert_evidence(self, tenant_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        evidence_id = str(evidence["evidence_id"])
        scoped_id = make_scoped_id(tenant_id, evidence_id)
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM evidence WHERE id = ?",
                (scoped_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO evidence (
                    id, tenant_id, evidence_id, asset_id, mission_id, checkpoint_name,
                    schema_version, image_path, raw_image_path, annotated_image_path,
                    media_type, timestamp_ns, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    asset_id = excluded.asset_id,
                    mission_id = excluded.mission_id,
                    checkpoint_name = excluded.checkpoint_name,
                    schema_version = excluded.schema_version,
                    image_path = excluded.image_path,
                    raw_image_path = excluded.raw_image_path,
                    annotated_image_path = excluded.annotated_image_path,
                    media_type = excluded.media_type,
                    timestamp_ns = excluded.timestamp_ns,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    scoped_id,
                    tenant_id,
                    evidence_id,
                    str(evidence.get("asset_id", "")),
                    evidence.get("mission_id"),
                    str(evidence.get("checkpoint_name", "")),
                    str(evidence.get("schema_version", "evidence.v1")),
                    evidence.get("image_path"),
                    evidence.get("raw_image_path"),
                    evidence.get("annotated_image_path"),
                    str(evidence.get("media_type", "image/png")),
                    evidence.get("timestamp_ns"),
                    _json_dump(evidence.get("metadata", {})),
                    created_at,
                    now,
                ),
            )
        return self.get_evidence(tenant_id, evidence_id)

    def get_evidence(self, tenant_id: str, evidence_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT evidence_id, asset_id, mission_id, checkpoint_name, schema_version,
                       image_path, raw_image_path, annotated_image_path, media_type,
                       timestamp_ns, metadata_json, created_at, updated_at
                FROM evidence
                WHERE tenant_id = ? AND evidence_id = ?
                """,
                (tenant_id, evidence_id),
            ).fetchone()
        if row is None:
            return None
        return self._evidence_row_to_dict(row)

    def _evidence_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = _json_load(data.pop("metadata_json", "{}"), {})
        return data

    def upsert_finding(self, tenant_id: str, finding: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        finding_id = str(finding["finding_id"])
        scoped_id = make_scoped_id(tenant_id, finding_id)
        with self.connect() as conn:
            existing = conn.execute(
                """
                SELECT created_at, status, assigned_to, acknowledged_by, resolved_by, resolution_note
                FROM findings
                WHERE id = ?
                """,
                (scoped_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            status_value = (
                existing["status"]
                if existing is not None
                else str(finding.get("status", "OPEN")).upper()
            )
            if status_value not in FINDING_STATUSES:
                status_value = "OPEN"
            conn.execute(
                """
                INSERT INTO findings (
                    id, tenant_id, finding_id, site_id, asset_id, mission_id, evidence_id,
                    schema_version, source_round_number, checkpoint_name, label, severity,
                    status, review_required, recommended_action, health_score, confidence,
                    outstanding, assigned_to, acknowledged_by, resolved_by, resolution_note,
                    detected_at, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    site_id = excluded.site_id,
                    asset_id = excluded.asset_id,
                    mission_id = excluded.mission_id,
                    evidence_id = excluded.evidence_id,
                    schema_version = excluded.schema_version,
                    source_round_number = excluded.source_round_number,
                    checkpoint_name = excluded.checkpoint_name,
                    label = excluded.label,
                    severity = excluded.severity,
                    review_required = excluded.review_required,
                    recommended_action = excluded.recommended_action,
                    health_score = excluded.health_score,
                    confidence = excluded.confidence,
                    outstanding = excluded.outstanding,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    scoped_id,
                    tenant_id,
                    finding_id,
                    str(finding.get("site_id", "factory_demo_site")),
                    str(finding.get("asset_id", "")),
                    finding.get("mission_id"),
                    finding.get("evidence_id"),
                    str(finding.get("schema_version", "finding.v1")),
                    finding.get("source_round_number"),
                    str(finding.get("checkpoint_name", "")),
                    str(finding.get("label", "unclassified_finding")),
                    str(finding.get("severity", "warning")),
                    status_value,
                    1 if finding.get("review_required", False) else 0,
                    finding.get("recommended_action"),
                    finding.get("health_score"),
                    finding.get("confidence"),
                    1 if finding.get("outstanding", True) else 0,
                    existing["assigned_to"] if existing else finding.get("assigned_to"),
                    existing["acknowledged_by"] if existing else finding.get("acknowledged_by"),
                    existing["resolved_by"] if existing else finding.get("resolved_by"),
                    existing["resolution_note"] if existing else finding.get("resolution_note"),
                    str(finding.get("detected_at", now)),
                    _json_dump(finding.get("metadata", {})),
                    created_at,
                    now,
                ),
            )
        return self.get_finding(tenant_id, finding_id)

    def list_findings(
        self,
        tenant_id: str,
        *,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [tenant_id]
        status_clause = ""
        if status_filter:
            status_clause = "AND f.status = ?"
            params.append(status_filter.upper())
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT f.finding_id, f.site_id, f.asset_id, f.mission_id, f.evidence_id,
                       f.schema_version, f.source_round_number, f.checkpoint_name, f.label,
                       f.severity, f.status, f.review_required, f.recommended_action,
                       f.health_score, f.confidence, f.outstanding, f.assigned_to,
                       f.acknowledged_by, f.resolved_by, f.resolution_note, f.detected_at,
                       f.metadata_json, f.created_at, f.updated_at,
                       a.name AS asset_name, a.zone AS asset_zone, a.criticality AS asset_criticality,
                       s.name AS site_name
                FROM findings f
                LEFT JOIN assets a
                    ON a.tenant_id = f.tenant_id AND a.asset_id = f.asset_id
                LEFT JOIN sites s
                    ON s.tenant_id = f.tenant_id AND s.site_id = f.site_id
                WHERE f.tenant_id = ?
                  {status_clause}
                ORDER BY
                    CASE f.status
                        WHEN 'OPEN' THEN 0
                        WHEN 'ACKNOWLEDGED' THEN 1
                        WHEN 'ASSIGNED' THEN 2
                        WHEN 'REINSPECTION_REQUESTED' THEN 3
                        ELSE 4
                    END,
                    CASE f.severity
                        WHEN 'critical' THEN 0
                        WHEN 'warning' THEN 1
                        ELSE 2
                    END,
                    f.updated_at DESC
                """,
                params,
            ).fetchall()
        return [self._finding_row_to_dict(row) for row in rows]

    def get_finding(self, tenant_id: str, finding_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT f.finding_id, f.site_id, f.asset_id, f.mission_id, f.evidence_id,
                       f.schema_version, f.source_round_number, f.checkpoint_name, f.label,
                       f.severity, f.status, f.review_required, f.recommended_action,
                       f.health_score, f.confidence, f.outstanding, f.assigned_to,
                       f.acknowledged_by, f.resolved_by, f.resolution_note, f.detected_at,
                       f.metadata_json, f.created_at, f.updated_at,
                       a.name AS asset_name, a.zone AS asset_zone, a.criticality AS asset_criticality,
                       s.name AS site_name
                FROM findings f
                LEFT JOIN assets a
                    ON a.tenant_id = f.tenant_id AND a.asset_id = f.asset_id
                LEFT JOIN sites s
                    ON s.tenant_id = f.tenant_id AND s.site_id = f.site_id
                WHERE f.tenant_id = ? AND f.finding_id = ?
                """,
                (tenant_id, finding_id),
            ).fetchone()
        if row is None:
            return None
        return self._finding_row_to_dict(row)

    def _finding_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["review_required"] = bool(data.get("review_required", 0))
        data["outstanding"] = bool(data.get("outstanding", 0))
        data["metadata"] = _json_load(data.pop("metadata_json", "{}"), {})
        return data

    def list_finding_events(self, tenant_id: str, finding_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, actor, note, payload_json, created_at
                FROM finding_events
                WHERE tenant_id = ? AND finding_id = ?
                ORDER BY created_at ASC
                """,
                (tenant_id, finding_id),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["payload"] = _json_load(event.pop("payload_json", "{}"), {})
            events.append(event)
        return events

    def record_finding_event(
        self,
        tenant_id: str,
        *,
        finding_id: str,
        event_id: str,
        event_type: str,
        actor: str,
        note: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO finding_events (id, tenant_id, finding_id, event_type, actor, note, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    tenant_id,
                    finding_id,
                    event_type,
                    actor,
                    note,
                    _json_dump(payload or {}),
                    utc_now_iso(),
                ),
            )

    def update_finding_action(
        self,
        tenant_id: str,
        *,
        finding_id: str,
        status_value: str,
        actor: str,
        note: str = "",
        assigned_to: str | None = None,
        outstanding: bool | None = None,
    ) -> dict[str, Any] | None:
        normalized_status = status_value.upper()
        if normalized_status not in FINDING_STATUSES:
            raise ValueError(f"Unsupported finding status: {status_value}")
        now = utc_now_iso()
        with self.connect() as conn:
            finding = conn.execute(
                """
                SELECT finding_id, assigned_to, acknowledged_by, resolved_by, resolution_note, outstanding
                FROM findings
                WHERE tenant_id = ? AND finding_id = ?
                """,
                (tenant_id, finding_id),
            ).fetchone()
            if finding is None:
                return None
            assigned_value = assigned_to if assigned_to is not None else finding["assigned_to"]
            acknowledged_by = finding["acknowledged_by"]
            resolved_by = finding["resolved_by"]
            resolution_note = finding["resolution_note"]
            outstanding_value = (
                finding["outstanding"] if outstanding is None else 1 if outstanding else 0
            )
            if normalized_status == "ACKNOWLEDGED":
                acknowledged_by = actor
            if normalized_status == "ASSIGNED":
                assigned_value = assigned_to or assigned_value or actor
            if normalized_status == "RESOLVED":
                resolved_by = actor
                resolution_note = note
                outstanding_value = 0
            if normalized_status in {"CLOSED", "REJECTED"}:
                outstanding_value = 0
            conn.execute(
                """
                UPDATE findings
                SET status = ?,
                    assigned_to = ?,
                    acknowledged_by = ?,
                    resolved_by = ?,
                    resolution_note = ?,
                    outstanding = ?,
                    updated_at = ?
                WHERE tenant_id = ? AND finding_id = ?
                """,
                (
                    normalized_status,
                    assigned_value,
                    acknowledged_by,
                    resolved_by,
                    resolution_note,
                    outstanding_value,
                    now,
                    tenant_id,
                    finding_id,
                ),
            )
        return self.get_finding(tenant_id, finding_id)

    def sync_asset_finding_outstanding(
        self,
        tenant_id: str,
        asset_id: str,
        *,
        outstanding: bool,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE findings
                SET outstanding = ?, updated_at = ?
                WHERE tenant_id = ? AND asset_id = ? AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED')
                """,
                (1 if outstanding else 0, utc_now_iso(), tenant_id, asset_id),
            )

    def record_sync_run(
        self,
        tenant_id: str,
        *,
        sync_id: str,
        source: str,
        status: str,
        summary: dict[str, Any],
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_runs (id, tenant_id, source, status, summary_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    sync_id,
                    tenant_id,
                    source,
                    status,
                    _json_dump(summary),
                    utc_now_iso(),
                ),
            )

    def get_latest_sync_run(self, tenant_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, source, status, summary_json, created_at
                FROM sync_runs
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["summary"] = _json_load(data.pop("summary_json", "{}"), {})
        return data

    def get_operator_summary(self, tenant_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            site_count = conn.execute(
                "SELECT COUNT(*) AS count FROM sites WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()["count"]
            asset_count = conn.execute(
                "SELECT COUNT(*) AS count FROM assets WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()["count"]
            open_findings = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM findings
                WHERE tenant_id = ? AND status IN ('OPEN', 'ACKNOWLEDGED', 'ASSIGNED', 'REINSPECTION_REQUESTED')
                """,
                (tenant_id,),
            ).fetchone()["count"]
            open_missions = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM missions
                WHERE tenant_id = ? AND status IN ('QUEUED', 'ACTIVE', 'PAUSED')
                """,
                (tenant_id,),
            ).fetchone()["count"]
            outstanding_assets = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM assets
                WHERE tenant_id = ? AND outstanding = 1
                """,
                (tenant_id,),
            ).fetchone()["count"]
        return {
            "site_count": int(site_count),
            "asset_count": int(asset_count),
            "open_findings": int(open_findings),
            "open_missions": int(open_missions),
            "outstanding_assets": int(outstanding_assets),
        }
