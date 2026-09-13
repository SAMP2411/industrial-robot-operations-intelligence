from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .storage import FleetWatchStore


@dataclass(frozen=True)
class BenchmarkSyncPaths:
    workspace_root: Path
    runtime_root: Path
    site_config_path: Path
    asset_registry_path: Path
    inspection_profiles_path: Path


def stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1("||".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    return data if isinstance(data, dict) else {}


def _normalize_site(site_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": str(site_data.get("schema_version", "site.v1")),
        "site_id": str(site_data.get("site_id", "factory_demo_site")),
        "name": str(site_data.get("name", "Factory Demo Warehouse")),
        "timezone": str(site_data.get("timezone", "UTC")),
        "map_id": str(site_data.get("map_id", "nav2_warehouse")),
        "coordinate_frame": str(site_data.get("coordinate_frame", "map")),
        "status": str(site_data.get("status", "ACTIVE")),
        "metadata": site_data.get("metadata", {}),
    }


def sync_latest_benchmark(
    *,
    store: FleetWatchStore,
    tenant_id: str,
    paths: BenchmarkSyncPaths,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []
    site_imported = 0
    asset_imported = 0
    mission_imported = 0
    finding_imported = 0
    evidence_imported = 0

    site_config = _normalize_site(_load_yaml(paths.site_config_path))
    store.upsert_site(tenant_id, site_config)
    site_imported = 1

    asset_registry = _load_yaml(paths.asset_registry_path)
    assets = asset_registry.get("assets", [])
    for raw_asset in assets:
        if not isinstance(raw_asset, dict):
            continue
        normalized_asset = dict(raw_asset)
        normalized_asset["schema_version"] = str(
            asset_registry.get("schema_version", normalized_asset.get("schema_version", "asset_registry.v1"))
        )
        store.upsert_asset(tenant_id, site_config["site_id"], normalized_asset)
        asset_imported += 1

    scenario_manifest = _load_json(paths.runtime_root / "scenario" / "scenario_manifest.json")
    campaign_state = _load_json(paths.runtime_root / "latest_campaign_state.json")
    round_reports = sorted(paths.runtime_root.glob("round_*_report.json"))

    if not round_reports:
        warnings.append(
            f"No round reports found under {paths.runtime_root}. Imported site and asset registry only."
        )

    for report_path in round_reports:
        report = _load_json(report_path)
        if not report:
            continue
        mission_id = str(report.get("mission_id", "")).strip() or stable_id(
            "mission",
            report.get("run_id", "no_run"),
            report.get("round_number", 0),
            report.get("mission_profile", "unknown_profile"),
        )
        mission_source = str(report.get("mission_source", "autonomous"))
        mission_type = str(report.get("mission_type", "")).strip() or (
            "routine_round"
            if report.get("mission_profile") != "targeted_follow_up"
            else "targeted_follow_up"
        )
        store.upsert_mission(
            tenant_id,
            {
                "mission_id": mission_id,
                "schema_version": "mission.v1",
                "site_id": site_config["site_id"],
                "run_id": report.get("run_id"),
                "scenario_id": report.get("scenario_id", scenario_manifest.get("scenario_id")),
                "round_number": report.get("round_number"),
                "mission_profile": report.get("mission_profile"),
                "mission_type": mission_type,
                "status": "COMPLETED" if report.get("success", False) else "FAILED",
                "mission_decision": report.get("mission_decision"),
                "decision_reason": report.get("decision_reason"),
                "priority": "high" if report.get("critical_count", 0) else "normal",
                "selected_assets": report.get("selected_assets", []),
                "follow_up_assets": report.get("follow_up_assets", []),
                "metadata": {
                    "source_file": str(report_path),
                    "mission_source": mission_source,
                    "action_result": report.get("action_result"),
                    "nav2_error_code": report.get("nav2_error_code"),
                    "duration_seconds": report.get("duration_seconds"),
                    "site_alert_level": report.get("site_alert_level"),
                    "success": report.get("success", False),
                },
            },
        )
        mission_imported += 1

        checkpoints = report.get("checkpoints", [])
        for checkpoint in checkpoints:
            if not isinstance(checkpoint, dict):
                continue
            is_detection = (
                checkpoint.get("is_anomaly", False)
                or checkpoint.get("review_required", False)
                or checkpoint.get("inspection_severity") in {"warning", "critical"}
            )
            if not is_detection:
                continue

            finding_asset_id = str(checkpoint.get("asset_id", "unmapped_asset"))
            evidence_id = stable_id(
                "evidence",
                report.get("run_id", "no_run"),
                report.get("round_number", 0),
                finding_asset_id,
                checkpoint.get("checkpoint_name", checkpoint.get("waypoint_index", 0)),
            )
            store.upsert_evidence(
                tenant_id,
                {
                    "evidence_id": evidence_id,
                    "schema_version": "evidence.v1",
                    "asset_id": finding_asset_id,
                    "mission_id": mission_id,
                    "checkpoint_name": checkpoint.get("checkpoint_name", ""),
                    "image_path": checkpoint.get("image_path"),
                    "raw_image_path": checkpoint.get("raw_image_path"),
                    "annotated_image_path": checkpoint.get("annotated_image_path"),
                    "media_type": "image/png",
                    "timestamp_ns": report.get("timestamp_ns"),
                    "metadata": {
                        "source_file": str(report_path),
                        "pose": checkpoint.get("pose", {}),
                        "ground_truth_label": checkpoint.get("ground_truth_label"),
                        "ground_truth_severity": checkpoint.get("ground_truth_severity"),
                        "matches_ground_truth": checkpoint.get("matches_ground_truth"),
                    },
                },
            )
            evidence_imported += 1

            finding_id = stable_id(
                "finding",
                report.get("run_id", "no_run"),
                report.get("round_number", 0),
                finding_asset_id,
                checkpoint.get("waypoint_index", 0),
                checkpoint.get("inspection_label", "unknown_label"),
            )
            store.upsert_finding(
                tenant_id,
                {
                    "finding_id": finding_id,
                    "schema_version": "finding.v1",
                    "site_id": site_config["site_id"],
                    "asset_id": finding_asset_id,
                    "mission_id": mission_id,
                    "evidence_id": evidence_id,
                    "source_round_number": report.get("round_number"),
                    "checkpoint_name": checkpoint.get("checkpoint_name", ""),
                    "label": checkpoint.get("inspection_label", "unclassified_finding"),
                    "severity": checkpoint.get("inspection_severity", "warning"),
                    "status": "OPEN",
                    "review_required": checkpoint.get("review_required", False),
                    "recommended_action": checkpoint.get("recommended_action"),
                    "health_score": checkpoint.get("health_score"),
                    "confidence": checkpoint.get("inspection_confidence"),
                    "outstanding": True,
                    "detected_at": started_at,
                    "metadata": {
                        "source_file": str(report_path),
                        "asset_display_name": checkpoint.get("asset_display_name"),
                        "asset_type": checkpoint.get("asset_type"),
                        "zone": checkpoint.get("zone"),
                        "asset_priority": checkpoint.get("asset_priority"),
                        "enabled_modalities": checkpoint.get("enabled_modalities", []),
                        "anomaly_sources": checkpoint.get("anomaly_sources", []),
                        "note": checkpoint.get("note", ""),
                        "thermal_delta_c": checkpoint.get("thermal_delta_c"),
                        "acoustic_db": checkpoint.get("acoustic_db"),
                        "gas_ppm": checkpoint.get("gas_ppm"),
                        "thermal_alert": checkpoint.get("thermal_alert", False),
                        "acoustic_alert": checkpoint.get("acoustic_alert", False),
                        "gas_alert": checkpoint.get("gas_alert", False),
                    },
                },
            )
            finding_imported += 1

    for trend in campaign_state.get("asset_trends", []):
        if not isinstance(trend, dict):
            continue
        asset_id = str(trend.get("asset_id", ""))
        if not asset_id:
            continue
        store.update_asset_runtime_state(
            tenant_id,
            asset_id,
            latest_label=trend.get("latest_label"),
            latest_severity=trend.get("latest_severity"),
            latest_health_score=trend.get("latest_health_score"),
            latest_confidence=trend.get("average_confidence"),
            latest_image_path=trend.get("latest_image_path"),
            latest_annotated_image_path=trend.get("latest_annotated_image_path"),
            outstanding=bool(trend.get("outstanding", False)),
        )
        store.sync_asset_finding_outstanding(
            tenant_id,
            asset_id,
            outstanding=bool(trend.get("outstanding", False)),
        )

    summary = {
        "schema_version": "benchmark_sync_summary.v1",
        "tenant_id": tenant_id,
        "site_id": site_config["site_id"],
        "site_name": site_config["name"],
        "started_at": started_at,
        "workspace_root": str(paths.workspace_root),
        "runtime_root": str(paths.runtime_root),
        "site_config_file": str(paths.site_config_path),
        "asset_registry_file": str(paths.asset_registry_path),
        "inspection_profiles_file": str(paths.inspection_profiles_path),
        "scenario_id": scenario_manifest.get("scenario_id") or campaign_state.get("scenario_id"),
        "run_id": campaign_state.get("run_id") or scenario_manifest.get("run_id"),
        "site_imported": site_imported,
        "asset_imported": asset_imported,
        "mission_imported": mission_imported,
        "finding_imported": finding_imported,
        "evidence_imported": evidence_imported,
        "warnings": warnings,
    }

    store.record_sync_run(
        tenant_id,
        sync_id=stable_id("sync", tenant_id, summary.get("run_id"), started_at),
        source="factory_inspection_benchmark",
        status="partial" if warnings else "success",
        summary=summary,
    )
    return summary
