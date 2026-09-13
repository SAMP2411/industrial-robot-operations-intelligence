from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .storage import FleetWatchStore, utc_now_iso


QUEUE_SCHEMA_VERSION = "operator_mission_queue.v1"
OPERATOR_MISSION_SOURCE = "operator_requested"
QUEUE_STATUSES = {
    "QUEUED",
    "ACTIVE",
    "PAUSED",
    "CANCELLED",
    "COMPLETED",
    "FAILED",
    "REJECTED",
}
TERMINAL_QUEUE_STATUSES = {"CANCELLED", "COMPLETED", "FAILED", "REJECTED"}


def normalize_queue_status(status_value: str | None) -> str:
    normalized = str(status_value or "QUEUED").upper()
    return normalized if normalized in QUEUE_STATUSES else "QUEUED"


def load_operator_queue(queue_path: Path) -> dict[str, Any]:
    if not queue_path.exists():
        return {"schema_version": QUEUE_SCHEMA_VERSION, "missions": []}
    data = yaml.safe_load(queue_path.read_text())
    if not isinstance(data, dict):
        return {"schema_version": QUEUE_SCHEMA_VERSION, "missions": []}
    missions = data.get("missions", [])
    if not isinstance(missions, list):
        missions = []
    return {
        "schema_version": str(data.get("schema_version", QUEUE_SCHEMA_VERSION)),
        "missions": missions,
    }


def save_operator_queue(queue_path: Path, document: dict[str, Any]) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": str(document.get("schema_version", QUEUE_SCHEMA_VERSION)),
        "missions": document.get("missions", []),
    }
    temp_path = queue_path.with_suffix(queue_path.suffix + ".tmp")
    temp_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    temp_path.replace(queue_path)


def list_operator_queue_missions(
    queue_path: Path,
    *,
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    missions = load_operator_queue(queue_path).get("missions", [])
    if tenant_id is None:
        return [mission for mission in missions if isinstance(mission, dict)]
    return [
        mission
        for mission in missions
        if isinstance(mission, dict) and str(mission.get("tenant_id", "")) == tenant_id
    ]


def is_operator_controlled_mission(mission: dict[str, Any] | None) -> bool:
    if not mission:
        return False
    metadata = mission.get("metadata", {})
    if isinstance(metadata, dict):
        if metadata.get("created_from") == "operator_console":
            return True
        if metadata.get("mission_source") == OPERATOR_MISSION_SOURCE:
            return True
    return str(mission.get("mission_type", "")) in {"manual_inspection", "reinspection"}


def upsert_operator_queue_mission(
    queue_path: Path,
    *,
    tenant_id: str,
    mission: dict[str, Any],
) -> dict[str, Any]:
    document = load_operator_queue(queue_path)
    missions = document["missions"]
    mission_id = str(mission["mission_id"])
    now = utc_now_iso()

    existing_index = next(
        (
            index
            for index, entry in enumerate(missions)
            if isinstance(entry, dict)
            and str(entry.get("tenant_id", "")) == tenant_id
            and str(entry.get("mission_id", "")) == mission_id
        ),
        None,
    )
    existing = missions[existing_index] if existing_index is not None else {}
    if not isinstance(existing, dict):
        existing = {}

    metadata = dict(existing.get("metadata", {}))
    incoming_metadata = mission.get("metadata", {})
    if isinstance(incoming_metadata, dict):
        metadata.update(incoming_metadata)

    entry = {
        "mission_id": mission_id,
        "tenant_id": tenant_id,
        "site_id": str(mission.get("site_id", existing.get("site_id", "factory_demo_site"))),
        "mission_source": str(
            mission.get("mission_source", existing.get("mission_source", OPERATOR_MISSION_SOURCE))
        ),
        "mission_type": str(mission.get("mission_type", existing.get("mission_type", "manual_inspection"))),
        "status": normalize_queue_status(mission.get("status", existing.get("status", "QUEUED"))),
        "priority": str(mission.get("priority", existing.get("priority", "normal"))),
        "selected_assets": list(
            dict.fromkeys(mission.get("selected_assets", existing.get("selected_assets", [])))
        ),
        "follow_up_assets": list(
            dict.fromkeys(mission.get("follow_up_assets", existing.get("follow_up_assets", [])))
        ),
        "linked_finding_id": mission.get("linked_finding_id", existing.get("linked_finding_id")),
        "requested_by": mission.get("requested_by", existing.get("requested_by")),
        "reason": str(
            mission.get(
                "reason",
                metadata.get("reason", existing.get("reason", "")),
            )
        ),
        "metadata": metadata,
        "created_at": str(existing.get("created_at", mission.get("created_at", now))),
        "updated_at": now,
        "activated_at": existing.get("activated_at"),
        "completed_at": existing.get("completed_at"),
        "run_id": mission.get("run_id", existing.get("run_id")),
        "scenario_id": mission.get("scenario_id", existing.get("scenario_id")),
        "round_number": mission.get("round_number", existing.get("round_number")),
        "mission_profile": mission.get("mission_profile", existing.get("mission_profile")),
        "mission_decision": mission.get("mission_decision", existing.get("mission_decision")),
        "decision_reason": mission.get("decision_reason", existing.get("decision_reason")),
        "latest_result": mission.get("latest_result", existing.get("latest_result", {})),
    }

    if entry["status"] == "ACTIVE" and not entry.get("activated_at"):
        entry["activated_at"] = now
    if entry["status"] in TERMINAL_QUEUE_STATUSES:
        entry["completed_at"] = now

    if existing_index is None:
        missions.append(entry)
    else:
        missions[existing_index] = entry

    save_operator_queue(queue_path, document)
    return entry


def update_operator_queue_mission(
    queue_path: Path,
    *,
    tenant_id: str,
    mission_id: str,
    status: str | None = None,
    **updates: Any,
) -> dict[str, Any] | None:
    document = load_operator_queue(queue_path)
    missions = document["missions"]
    now = utc_now_iso()

    for index, mission in enumerate(missions):
        if not isinstance(mission, dict):
            continue
        if str(mission.get("tenant_id", "")) != tenant_id:
            continue
        if str(mission.get("mission_id", "")) != mission_id:
            continue

        entry = dict(mission)
        if status is not None:
            entry["status"] = normalize_queue_status(status)

        for key, value in updates.items():
            if value is None:
                continue
            entry[key] = value

        entry["updated_at"] = now
        if entry.get("status") == "ACTIVE" and not entry.get("activated_at"):
            entry["activated_at"] = now
        if entry.get("status") in TERMINAL_QUEUE_STATUSES:
            entry["completed_at"] = now

        missions[index] = entry
        save_operator_queue(queue_path, document)
        return entry

    return None


def sync_operator_queue_to_store(
    *,
    store: FleetWatchStore,
    tenant_id: str,
    queue_path: Path,
) -> int:
    updated = 0
    for queued_mission in list_operator_queue_missions(queue_path, tenant_id=tenant_id):
        mission_id = str(queued_mission.get("mission_id", ""))
        if not mission_id:
            continue

        existing = store.get_mission(tenant_id, mission_id) or {}
        metadata = dict(existing.get("metadata", {}))
        queued_metadata = queued_mission.get("metadata", {})
        if isinstance(queued_metadata, dict):
            metadata.update(queued_metadata)
        metadata["mission_source"] = queued_mission.get("mission_source", OPERATOR_MISSION_SOURCE)
        metadata["operator_queue_status"] = queued_mission.get("status", "QUEUED")
        if queued_mission.get("reason"):
            metadata["reason"] = queued_mission["reason"]
        if queued_mission.get("activated_at"):
            metadata["activated_at"] = queued_mission["activated_at"]
        if queued_mission.get("completed_at"):
            metadata["completed_at"] = queued_mission["completed_at"]
        if queued_mission.get("latest_result"):
            metadata["latest_result"] = queued_mission["latest_result"]

        store.upsert_mission(
            tenant_id,
            {
                "mission_id": mission_id,
                "schema_version": existing.get("schema_version", "mission.v1"),
                "site_id": queued_mission.get("site_id", existing.get("site_id", "factory_demo_site")),
                "run_id": queued_mission.get("run_id", existing.get("run_id")),
                "scenario_id": queued_mission.get("scenario_id", existing.get("scenario_id")),
                "round_number": queued_mission.get("round_number", existing.get("round_number")),
                "mission_profile": queued_mission.get(
                    "mission_profile",
                    existing.get("mission_profile", queued_mission.get("mission_source")),
                ),
                "mission_type": queued_mission.get(
                    "mission_type",
                    existing.get("mission_type", "manual_inspection"),
                ),
                "status": queued_mission.get("status", existing.get("status", "QUEUED")),
                "mission_decision": queued_mission.get(
                    "mission_decision",
                    existing.get("mission_decision"),
                ),
                "decision_reason": queued_mission.get(
                    "decision_reason",
                    existing.get("decision_reason"),
                ),
                "priority": queued_mission.get("priority", existing.get("priority", "normal")),
                "selected_assets": queued_mission.get(
                    "selected_assets",
                    existing.get("selected_assets", []),
                ),
                "follow_up_assets": queued_mission.get(
                    "follow_up_assets",
                    existing.get("follow_up_assets", []),
                ),
                "linked_finding_id": queued_mission.get(
                    "linked_finding_id",
                    existing.get("linked_finding_id"),
                ),
                "requested_by": queued_mission.get("requested_by", existing.get("requested_by")),
                "metadata": metadata,
            },
        )
        updated += 1

    return updated
