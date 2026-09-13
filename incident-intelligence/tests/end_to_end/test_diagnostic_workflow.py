from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from sqlalchemy import select

from packages.data_quality import assess_incident
from packages.domain_models.models import Asset, Customer, DataSource, DiagnosticEngagement, EvidenceLink, Incident, RawRecord, RootCauseHypothesis, Site, System
from packages.hypothesis_engine import recalculate_confidence
from packages.incident_engine import create_downtime_segment, create_recovery_action
from packages.ingestion_core import IngestionService
from packages.report_generation import approve_report_version, generate_report_bundle
from packages.timeline_engine import TimelineFilters, build_timeline, update_clock_offset


ROOT = Path(__file__).resolve().parents[2]


def test_three_source_incident_to_approved_vendor_package(db_session, tmp_path: Path):
    customer = Customer(name="Synthetic Fixture Only")
    db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Simulation Lab", timezone="UTC")
    db_session.add(site); db_session.flush()
    system = System(site_id=site.id, name="AMR Fleet", system_type="amr_fleet")
    db_session.add(system); db_session.flush()
    for external_id, name, asset_type in [("AMR-07", "Robot 07", "amr"), ("DOOR-04", "Door 04", "door"), ("WIFI-ZONE-A", "Wi-Fi Zone A", "network_zone")]:
        db_session.add(Asset(site_id=site.id, system_id=system.id, name=name, asset_type=asset_type, external_asset_id=external_id))
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Door and Wi-Fi ambiguity")
    db_session.add(engagement); db_session.flush()
    fixture = ROOT / "fixtures/incident_001_door_wifi"
    source_specs = [("Robot", "robot_controller", "robot.csv", 0), ("Fleet", "fleet_manager", "fleet.json", 0), ("Infrastructure", "infrastructure", "door_wifi.jsonl", 3400)]
    service = IngestionService(db_session, tmp_path / "uploads")
    for name, source_type, filename, offset in source_specs:
        source = DataSource(engagement_id=engagement.id, name=name, source_type=source_type, clock_offset_ms=offset)
        db_session.add(source); db_session.flush()
        content = (fixture / filename).read_bytes()
        run = service.create_run(data_source_id=source.id, filename=filename, content=content, mime_type="text/plain", mapping={}, idempotency_key=f"fixture:{filename}", actor="analyst")
        assert service.commit(run.id, actor="analyst")["events_normalized"] >= 2
    incident = Incident(diagnostic_engagement_id=engagement.id, site_id=site.id, title="AMR blocked at Door 04", description="Synthetic multi-source incident.", status="review", started_at=datetime(2026, 4, 7, 9, 12, 50, tzinfo=timezone.utc), recovered_at=datetime(2026, 4, 7, 9, 13, 30, tzinfo=timezone.utc), business_impact="One robot blocked for 20 seconds", created_by="analyst")
    db_session.add(incident); db_session.commit()
    timeline = build_timeline(db_session, incident, TimelineFilters())
    assert len(timeline) >= 7
    assert len({item["source"]["name"] for item in timeline}) == 3
    infra = db_session.scalar(select(DataSource).where(DataSource.name == "Infrastructure"))
    before = [item["id"] for item in timeline]
    assert update_clock_offset(db_session, infra.id, 0, reason="Aligned shared door-open event", actor="analyst") == 3
    after = [item["id"] for item in build_timeline(db_session, incident, TimelineFilters())]
    assert before != after
    create_downtime_segment(db_session, incident, {"started_at": datetime(2026, 4, 7, 9, 13, 5, tzinfo=timezone.utc), "ended_at": datetime(2026, 4, 7, 9, 13, 24, tzinfo=timezone.utc), "segment_type": "blocked_robot", "affected_asset_ids": [], "business_impact": "Robot blocked", "evidence_links": [], "analyst_approved": True}, actor="analyst")
    create_recovery_action(db_session, incident, {"action_type": "mission retry", "performed_at": datetime(2026, 4, 7, 9, 13, 18, tzinfo=timezone.utc), "performed_by": "operator", "asset_id": None, "source": "fleet log", "outcome": "Mission resumed", "evidence_links": []}, actor="analyst")
    hypothesis = RootCauseHypothesis(incident_id=incident.id, title="Wi-Fi roaming delayed door coordination", failure_domain="network/Wi-Fi", description="Timing suggests a network contribution but WCS trace is missing.", analyst_owner="analyst")
    db_session.add(hypothesis); db_session.flush()
    raw_records = db_session.scalars(select(RawRecord).limit(3)).all()
    db_session.add_all([
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, raw_record_id=raw_records[0].id, relation="supports", analyst_note="Wi-Fi roaming overlaps the stop", weight=2, created_by="analyst"),
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, raw_record_id=raw_records[1].id, relation="contradicts", analyst_note="Door PLC received a release request", weight=1, review_status="reviewed", contradiction_resolution="Retained as a material alternative explanation", created_by="analyst"),
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="missing_expected", analyst_note="WCS network trace unavailable", weight=1, created_by="analyst"),
    ])
    db_session.commit()
    assert 0 < recalculate_confidence(db_session, hypothesis) < 1
    quality = assess_incident(db_session, incident)
    assert quality["schema_version"] == "1.0"
    result = generate_report_bundle(db_session, incident, tmp_path / "reports", actor="analyst", included_raw_record_ids=[raw_records[0].id])
    assert {item["format"] for item in result["artifacts"]} == {"json", "markdown", "html", "pdf", "timeline_csv", "vendor_zip"}
    approved = approve_report_version(db_session, incident, result["version"], actor="reviewer", note="Evidence checked")
    assert all(item.immutable for item in approved)
    zip_path = Path(next(item.storage_path for item in approved if item.format == "vendor_zip"))
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert {"incident_summary.md", "timeline.csv", "evidence_manifest.json", "questions_for_vendor.md"} <= names
        manifest = json.loads(archive.read("evidence_manifest.json"))
        assert manifest["files"][0]["sha256"]
