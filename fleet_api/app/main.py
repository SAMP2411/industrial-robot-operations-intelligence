from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import os
import re
import secrets
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, model_validator

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:  # pragma: no cover - optional dependency fallback
    InfluxDBClient = None
    Point = None
    WritePrecision = None
    SYNCHRONOUS = None

from .inspection_sync import BenchmarkSyncPaths, stable_id, sync_latest_benchmark
from .operator_dispatch import (
    is_operator_controlled_mission,
    sync_operator_queue_to_store,
    update_operator_queue_mission,
    upsert_operator_queue_mission,
)
from .storage import FleetWatchStore, utc_now_iso


@dataclass(frozen=True)
class AppSettings:
    workspace_root: Path
    fleetwatch_root: Path
    ui_path: Path
    sqlite_path: Path
    runtime_root: Path
    operator_queue_path: Path
    site_config_path: Path
    asset_registry_path: Path
    inspection_profiles_path: Path
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str
    ingest_api_key: str
    demo_email: str
    demo_password: str
    demo_company: str
    demo_tenant_id: str
    secret_key: str
    cors_origins: list[str]
    token_expire_minutes: int = 60 * 24
    app_version: str = "0.2.0"


@dataclass
class InfluxHandles:
    client: Any | None
    write_api: Any | None
    query_api: Any | None
    status: str


def build_settings() -> AppSettings:
    workspace_root = Path(__file__).resolve().parents[2]
    fleetwatch_root = Path(__file__).resolve().parents[1]
    return AppSettings(
        workspace_root=workspace_root,
        fleetwatch_root=fleetwatch_root,
        ui_path=fleetwatch_root / "ui" / "Fleetwatch.html",
        sqlite_path=Path(
            os.getenv("FLEETWATCH_SQLITE_PATH", str(fleetwatch_root / "data" / "fleetwatch.db"))
        ).expanduser(),
        runtime_root=Path(
            os.getenv("FACTORY_BENCHMARK_RUNTIME_ROOT", "~/.ros/factory_inspection/benchmark")
        ).expanduser(),
        operator_queue_path=Path(
            os.getenv(
                "FACTORY_OPERATOR_QUEUE_PATH",
                "~/.ros/factory_inspection/operator/operator_mission_queue.yaml",
            )
        ).expanduser(),
        site_config_path=Path(
            os.getenv(
                "FACTORY_SITE_CONFIG",
                str(
                    workspace_root
                    / "src"
                    / "factory_inspection_mission"
                    / "config"
                    / "sites"
                    / "benchmark_site.yaml"
                ),
            )
        ).expanduser(),
        asset_registry_path=Path(
            os.getenv(
                "FACTORY_ASSET_REGISTRY",
                str(
                    workspace_root
                    / "src"
                    / "factory_inspection_mission"
                    / "config"
                    / "assets"
                    / "benchmark_asset_registry.yaml"
                ),
            )
        ).expanduser(),
        inspection_profiles_path=Path(
            os.getenv(
                "FACTORY_INSPECTION_PROFILES",
                str(
                    workspace_root
                    / "src"
                    / "factory_inspection_mission"
                    / "config"
                    / "inspection_profiles"
                    / "benchmark_inspection_profiles.yaml"
                ),
            )
        ).expanduser(),
        influx_url=os.getenv("INFLUX_URL", "http://localhost:8086"),
        influx_token=os.getenv("INFLUX_TOKEN", ""),
        influx_org=os.getenv("INFLUX_ORG", "startup-robot-dashboard"),
        influx_bucket=os.getenv("INFLUX_BUCKET", "robot_fleet"),
        ingest_api_key=os.getenv("INGEST_API_KEY", ""),
        demo_email=os.getenv("DEMO_EMAIL", ""),
        demo_password=os.getenv("DEMO_PASSWORD", ""),
        demo_company=os.getenv("DEMO_COMPANY", "FleetWatch"),
        demo_tenant_id=os.getenv("DEMO_TENANT_ID", "tenant_fleetwatch"),
        secret_key=os.getenv("SECRET_KEY") or secrets.token_urlsafe(48),
        cors_origins=[
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:8000,http://127.0.0.1:8000",
            ).split(",")
            if origin.strip()
        ],
    )


class RegisterRequest(BaseModel):
    email: str
    password: str
    company: str
    robots: list[str] = Field(
        default_factory=lambda: ["AMR-01", "AMR-02", "AMR-03", "AMR-04", "AMR-05"]
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class RobotTelemetry(BaseModel):
    battery: float
    status: Literal["idle", "moving", "charging", "fault"]
    x: float
    y: float
    speed: float
    tasks_done: int
    fault_code: Optional[str] = None
    uptime_s: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_fault(self):
        if self.status == "fault" and not self.fault_code:
            raise ValueError("fault_code is required when status is fault")
        if self.status != "fault" and self.fault_code:
            raise ValueError("fault_code is only valid when status is fault")
        return self


class ManualMissionRequest(BaseModel):
    asset_ids: list[str]
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    reason: str = Field(min_length=3)
    mission_type: str = "manual_inspection"


class ActionRequest(BaseModel):
    actor: Optional[str] = None
    note: str = ""


class AssignRequest(ActionRequest):
    assignee: str = Field(min_length=1)


class ResolveRequest(ActionRequest):
    resolution_note: str = Field(min_length=1)


class ReinspectRequest(ActionRequest):
    priority: Literal["low", "normal", "high", "critical"] = "high"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
ALGORITHM = "HS256"


def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def flux_string(value: str) -> str:
    return f'"{value.replace("\\", "\\\\").replace("\"", "\\\"")}"'


def create_influx_handles(settings: AppSettings) -> InfluxHandles:
    if InfluxDBClient is None:
        return InfluxHandles(None, None, None, "library_missing")
    if not settings.influx_token:
        return InfluxHandles(None, None, None, "unconfigured")
    try:
        client = InfluxDBClient(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        query_api = client.query_api()
        return InfluxHandles(client, write_api, query_api, "configured")
    except Exception:
        return InfluxHandles(None, None, None, "degraded")


def create_app(settings: AppSettings | None = None) -> FastAPI:
    settings = settings or build_settings()
    store = FleetWatchStore(settings.sqlite_path)
    store.init_db()
    influx_handles = create_influx_handles(settings)

    if settings.demo_email and settings.demo_password:
        store.ensure_user(
            email=settings.demo_email,
            hashed_password=hash_password(settings.demo_password),
            tenant_id=settings.demo_tenant_id,
            company=settings.demo_company,
            robots=["AMR-01", "AMR-02", "AMR-03", "AMR-04", "AMR-05"],
        )

    app = FastAPI(
        title="FleetWatch Operator API",
        description=(
            "Fleet telemetry plus inspection operations for the autonomous factory "
            "inspection benchmark."
        ),
        version=settings.app_version,
    )
    app.state.settings = settings
    app.state.store = store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def create_token(data: dict[str, Any]) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(timezone.utc) + timedelta(
            minutes=settings.token_expire_minutes
        )
        return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

    def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            user = store.get_user_by_email(email)
            if user is None:
                raise credentials_exception
            return user
        except JWTError as exc:
            raise credentials_exception from exc

    def require_influx() -> InfluxHandles:
        if influx_handles.query_api is None or influx_handles.write_api is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Fleet telemetry backend is unavailable. Inspection operator APIs still work, "
                    "but Influx-backed robot telemetry is not configured."
                ),
            )
        return influx_handles

    def enrich_evidence(evidence: dict[str, Any] | None) -> dict[str, Any] | None:
        if evidence is None:
            return None
        evidence_id = evidence["evidence_id"]
        evidence["primary_url"] = f"/api/v1/evidence/{evidence_id}/primary"
        evidence["annotated_url"] = f"/api/v1/evidence/{evidence_id}/annotated"
        evidence["raw_url"] = f"/api/v1/evidence/{evidence_id}/raw"
        return evidence

    def enrich_finding(finding: dict[str, Any]) -> dict[str, Any]:
        if finding.get("evidence_id"):
            finding["evidence_url"] = f"/api/v1/evidence/{finding['evidence_id']}"
            finding["evidence_image_url"] = f"/api/v1/evidence/{finding['evidence_id']}/primary"
        return finding

    def get_actor(user: dict[str, Any], actor_override: str | None) -> str:
        return actor_override.strip() if actor_override else str(user["email"])

    def get_first_site_id(tenant_id: str) -> str:
        sites = store.list_sites(tenant_id)
        if sites:
            return str(sites[0]["site_id"])
        return "factory_demo_site"

    def refresh_operator_state(tenant_id: str) -> None:
        sync_operator_queue_to_store(
            store=store,
            tenant_id=tenant_id,
            queue_path=settings.operator_queue_path,
        )

    def serve_evidence_variant(
        tenant_id: str,
        evidence_id: str,
        variant: str,
    ) -> FileResponse:
        evidence = store.get_evidence(tenant_id, evidence_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="Evidence not found")
        path_value = {
            "primary": evidence.get("annotated_image_path") or evidence.get("image_path"),
            "annotated": evidence.get("annotated_image_path"),
            "raw": evidence.get("raw_image_path"),
        }.get(variant)
        if not path_value:
            raise HTTPException(status_code=404, detail=f"No {variant} image recorded")
        image_path = Path(path_value)
        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Evidence file is missing on disk: {image_path}",
            )
        return FileResponse(image_path)

    @app.post("/auth/register", tags=["auth"])
    def register(req: RegisterRequest):
        if store.get_user_by_email(req.email) is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        company_slug = re.sub(r"[^a-z0-9]+", "_", req.company.lower()).strip("_")
        if not company_slug:
            raise HTTPException(
                status_code=400,
                detail="Company must contain letters or numbers",
            )
        tenant_id = f"tenant_{company_slug}_{secrets.token_hex(4)}"
        store.create_user(
            email=req.email,
            hashed_password=hash_password(req.password),
            tenant_id=tenant_id,
            company=req.company,
            robots=req.robots,
        )
        return {"message": "Account created", "tenant_id": tenant_id}

    @app.post("/auth/token", response_model=Token, tags=["auth"])
    def login(form: OAuth2PasswordRequestForm = Depends()):
        user = store.get_user_by_email(form.username)
        if user is None or not verify_password(form.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        token = create_token({"sub": user["email"]})
        return {"access_token": token, "token_type": "bearer"}

    @app.get("/fleet/robots", tags=["fleet"])
    def list_robots(user: dict[str, Any] = Depends(get_current_user)):
        robots = store.list_tenant_robots(user["tenant_id"])
        return {"tenant": user["company"], "robots": robots, "count": len(robots)}

    @app.get("/fleet/robots/{robot_id}", tags=["fleet"])
    def get_robot(robot_id: str, user: dict[str, Any] = Depends(get_current_user)):
        handles = require_influx()
        robots = store.list_tenant_robots(user["tenant_id"])
        if robot_id not in robots:
            raise HTTPException(status_code=404, detail="Robot not in your fleet")
        tenant_filter = flux_string(user["tenant_id"])
        robot_filter = flux_string(robot_id)
        flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r.tenant_id == {tenant_filter} and r.robot_id == {robot_filter})
  |> last()
"""
        tables = handles.query_api.query(flux, org=settings.influx_org)
        result = {"robot_id": robot_id, "metrics": {}}
        for table in tables:
            for record in table.records:
                result["metrics"][
                    f"{record.get_measurement()}.{record.get_field()}"
                ] = record.get_value()
        return result

    @app.get("/fleet/summary", tags=["fleet"])
    def fleet_summary(user: dict[str, Any] = Depends(get_current_user)):
        handles = require_influx()
        robots = store.list_tenant_robots(user["tenant_id"])
        robot_filter = " or ".join(
            [f"r.robot_id == {flux_string(robot_id)}" for robot_id in robots]
        ) or "false"
        tenant_filter = f"r.tenant_id == {flux_string(user['tenant_id'])}"

        queries = {
            "avg_battery_pct": f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "battery" and r._field == "soc_pct")
  |> filter(fn: (r) => {tenant_filter})
  |> filter(fn: (r) => {robot_filter})
  |> last()
  |> group()
  |> mean()
""",
            "total_tasks": f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "tasks" and r._field == "completed_total")
  |> filter(fn: (r) => {tenant_filter})
  |> filter(fn: (r) => {robot_filter})
  |> last()
  |> group()
  |> sum()
""",
            "active_faults": f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "robot_status" and r._field == "fault_code")
  |> filter(fn: (r) => {tenant_filter})
  |> filter(fn: (r) => {robot_filter})
  |> last()
  |> filter(fn: (r) => r._value != "none")
  |> group()
  |> count()
""",
            "online_robots": f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "robot_status" and r._field == "status")
  |> filter(fn: (r) => {tenant_filter})
  |> filter(fn: (r) => {robot_filter})
  |> last()
  |> group()
  |> count()
""",
        }

        def first_value(flux_query: str, default: int | float = 0) -> int | float:
            try:
                tables = handles.query_api.query(flux_query, org=settings.influx_org)
                for table in tables:
                    for record in table.records:
                        return record.get_value()
            except Exception:
                return default
            return default

        avg_battery = first_value(queries["avg_battery_pct"], 0.0)
        total_tasks = first_value(queries["total_tasks"], 0)
        active_faults = first_value(queries["active_faults"], 0)
        online_robots = first_value(queries["online_robots"], 0)
        online_count = min(len(robots), int(online_robots) if online_robots else 0)
        fault_count = min(online_count, int(active_faults) if active_faults else 0)
        return {
            "tenant": user["company"],
            "robot_count": len(robots),
            "online_robots": online_count,
            "offline_robots": len(robots) - online_count,
            "avg_battery_pct": round(float(avg_battery), 1) if avg_battery else 0.0,
            "total_tasks": int(total_tasks) if total_tasks else 0,
            "active_faults": fault_count,
            "fleet_uptime_pct": round(
                ((online_count - fault_count) / len(robots) * 100) if robots else 0.0,
                1,
            ),
            "timestamp": utc_now_iso(),
        }

    @app.get("/fleet/faults", tags=["fleet"])
    def fault_log(
        limit: int = Query(default=20, ge=1, le=200),
        user: dict[str, Any] = Depends(get_current_user),
    ):
        handles = require_influx()
        robots = store.list_tenant_robots(user["tenant_id"])
        robot_filter = " or ".join(
            [f"r.robot_id == {flux_string(robot_id)}" for robot_id in robots]
        ) or "false"
        tenant_filter = f"r.tenant_id == {flux_string(user['tenant_id'])}"
        flux = f"""
from(bucket: "{settings.influx_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "robot_status" and r._field == "fault_code")
  |> filter(fn: (r) => {tenant_filter})
  |> filter(fn: (r) => {robot_filter})
  |> filter(fn: (r) => r._value != "none")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
"""
        tables = handles.query_api.query(flux, org=settings.influx_org)
        faults: list[dict[str, Any]] = []
        for table in tables:
            for record in table.records:
                faults.append(
                    {
                        "robot_id": record.values.get("robot_id"),
                        "fault_code": record.get_value(),
                        "timestamp": record.get_time().isoformat(),
                    }
                )
        return {"faults": faults, "count": len(faults)}

    @app.post("/ingest/{robot_id}", tags=["ingest"])
    def ingest(
        robot_id: str,
        telemetry: RobotTelemetry,
        x_api_key: str = Header(default="", alias="X-API-Key"),
        x_tenant_id: str = Header(default="", alias="X-Tenant-ID"),
    ):
        handles = require_influx()
        if not settings.ingest_api_key:
            raise HTTPException(
                status_code=503,
                detail="Telemetry ingestion is not configured",
            )
        if not secrets.compare_digest(x_api_key, settings.ingest_api_key):
            raise HTTPException(status_code=401, detail="Invalid ingestion API key")
        if not re.fullmatch(r"tenant_[a-z0-9_]+", x_tenant_id):
            raise HTTPException(status_code=400, detail="Invalid tenant ID")

        ts = datetime.now(timezone.utc)
        status_point = (
            Point("robot_status")
            .tag("tenant_id", x_tenant_id)
            .tag("robot_id", robot_id)
            .field("status", telemetry.status)
            .field("fault_code", telemetry.fault_code or "none")
            .time(ts, WritePrecision.S)
        )
        if telemetry.uptime_s is not None:
            status_point.field("uptime_s", telemetry.uptime_s)
        points = [
            status_point,
            Point("battery")
            .tag("tenant_id", x_tenant_id)
            .tag("robot_id", robot_id)
            .field("soc_pct", float(telemetry.battery))
            .time(ts, WritePrecision.S),
            Point("odometry")
            .tag("tenant_id", x_tenant_id)
            .tag("robot_id", robot_id)
            .field("x_m", float(telemetry.x))
            .field("y_m", float(telemetry.y))
            .field("speed_ms", float(telemetry.speed))
            .time(ts, WritePrecision.S),
            Point("tasks")
            .tag("tenant_id", x_tenant_id)
            .tag("robot_id", robot_id)
            .field("completed_total", int(telemetry.tasks_done))
            .time(ts, WritePrecision.S),
        ]
        handles.write_api.write(
            bucket=settings.influx_bucket,
            org=settings.influx_org,
            record=points,
        )
        return {"status": "ok", "robot_id": robot_id, "timestamp": ts.isoformat()}

    @app.get("/api/v1/operator/summary", tags=["operator"])
    def operator_summary(user: dict[str, Any] = Depends(get_current_user)):
        refresh_operator_state(user["tenant_id"])
        summary = store.get_operator_summary(user["tenant_id"])
        latest_sync = store.get_latest_sync_run(user["tenant_id"])
        response = {
            "tenant": user["company"],
            "tenant_id": user["tenant_id"],
            **summary,
            "latest_sync": latest_sync,
            "timestamp": utc_now_iso(),
        }
        try:
            response["fleet"] = fleet_summary(user)
        except HTTPException:
            response["fleet"] = {
                "status": "unavailable",
                "reason": "Influx telemetry backend is not configured",
            }
        return response

    @app.post("/api/v1/sync/benchmark/latest", tags=["operator"])
    def sync_benchmark_latest(user: dict[str, Any] = Depends(get_current_user)):
        summary = sync_latest_benchmark(
            store=store,
            tenant_id=user["tenant_id"],
            paths=BenchmarkSyncPaths(
                workspace_root=settings.workspace_root,
                runtime_root=settings.runtime_root,
                site_config_path=settings.site_config_path,
                asset_registry_path=settings.asset_registry_path,
                inspection_profiles_path=settings.inspection_profiles_path,
            ),
        )
        return summary

    @app.get("/api/v1/sites", tags=["inspection"])
    def list_sites_v1(user: dict[str, Any] = Depends(get_current_user)):
        return {"sites": store.list_sites(user["tenant_id"])}

    @app.get("/api/v1/assets", tags=["inspection"])
    def list_assets_v1(user: dict[str, Any] = Depends(get_current_user)):
        assets = store.list_assets(user["tenant_id"])
        for asset in assets:
            if asset.get("latest_annotated_image_path"):
                asset["latest_image_url"] = (
                    f"/api/v1/evidence/by-asset/{asset['asset_id']}/annotated"
                )
        return {"assets": assets, "count": len(assets)}

    @app.get("/api/v1/assets/{asset_id}", tags=["inspection"])
    def get_asset_v1(asset_id: str, user: dict[str, Any] = Depends(get_current_user)):
        asset = store.get_asset(user["tenant_id"], asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        related_findings = [
            finding
            for finding in store.list_findings(user["tenant_id"])
            if finding["asset_id"] == asset_id
        ]
        asset["findings"] = [enrich_finding(finding) for finding in related_findings]
        return asset

    @app.get("/api/v1/missions", tags=["inspection"])
    def list_missions_v1(user: dict[str, Any] = Depends(get_current_user)):
        refresh_operator_state(user["tenant_id"])
        missions = store.list_missions(user["tenant_id"])
        return {"missions": missions, "count": len(missions)}

    @app.post("/api/v1/missions", tags=["inspection"])
    def create_mission_v1(
        req: ManualMissionRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        known_assets = {asset["asset_id"] for asset in store.list_assets(user["tenant_id"])}
        missing_assets = [asset_id for asset_id in req.asset_ids if asset_id not in known_assets]
        if missing_assets:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown assets for this tenant: {', '.join(missing_assets)}",
            )
        mission_id = stable_id("manual_mission", user["tenant_id"], utc_now_iso(), ",".join(req.asset_ids))
        mission = store.upsert_mission(
            user["tenant_id"],
            {
                "mission_id": mission_id,
                "schema_version": "mission.v1",
                "site_id": get_first_site_id(user["tenant_id"]),
                "mission_profile": "operator_requested",
                "mission_type": req.mission_type,
                "status": "QUEUED",
                "priority": req.priority,
                "selected_assets": req.asset_ids,
                "follow_up_assets": [],
                "requested_by": user["email"],
                "metadata": {"reason": req.reason, "created_from": "operator_console"},
            },
        )
        upsert_operator_queue_mission(
            settings.operator_queue_path,
            tenant_id=user["tenant_id"],
            mission={
                **mission,
                "mission_source": "operator_requested",
                "reason": req.reason,
            },
        )
        refresh_operator_state(user["tenant_id"])
        return store.get_mission(user["tenant_id"], mission_id)

    @app.post("/api/v1/missions/{mission_id}/pause", tags=["inspection"])
    def pause_mission_v1(mission_id: str, user: dict[str, Any] = Depends(get_current_user)):
        refresh_operator_state(user["tenant_id"])
        mission = store.get_mission(user["tenant_id"], mission_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Mission not found")
        if not is_operator_controlled_mission(mission):
            raise HTTPException(
                status_code=409,
                detail="Only operator-created missions can be paused from FleetWatch.",
            )
        if mission["status"] != "QUEUED":
            raise HTTPException(
                status_code=409,
                detail="Only queued missions can be paused in this iteration.",
            )
        store.update_mission_status(user["tenant_id"], mission_id, "PAUSED")
        update_operator_queue_mission(
            settings.operator_queue_path,
            tenant_id=user["tenant_id"],
            mission_id=mission_id,
            status="PAUSED",
        )
        refresh_operator_state(user["tenant_id"])
        return store.get_mission(user["tenant_id"], mission_id)

    @app.post("/api/v1/missions/{mission_id}/cancel", tags=["inspection"])
    def cancel_mission_v1(mission_id: str, user: dict[str, Any] = Depends(get_current_user)):
        refresh_operator_state(user["tenant_id"])
        mission = store.get_mission(user["tenant_id"], mission_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Mission not found")
        if not is_operator_controlled_mission(mission):
            raise HTTPException(
                status_code=409,
                detail="Only operator-created missions can be cancelled from FleetWatch.",
            )
        if mission["status"] not in {"QUEUED", "PAUSED"}:
            raise HTTPException(
                status_code=409,
                detail="Dispatched missions cannot be cancelled mid-round in this iteration.",
            )
        store.update_mission_status(user["tenant_id"], mission_id, "CANCELLED")
        update_operator_queue_mission(
            settings.operator_queue_path,
            tenant_id=user["tenant_id"],
            mission_id=mission_id,
            status="CANCELLED",
        )
        refresh_operator_state(user["tenant_id"])
        return store.get_mission(user["tenant_id"], mission_id)

    @app.get("/api/v1/findings", tags=["inspection"])
    def list_findings_v1(
        status_filter: Optional[str] = Query(default=None),
        user: dict[str, Any] = Depends(get_current_user),
    ):
        findings = store.list_findings(user["tenant_id"], status_filter=status_filter)
        return {"findings": [enrich_finding(finding) for finding in findings], "count": len(findings)}

    @app.get("/api/v1/findings/{finding_id}", tags=["inspection"])
    def get_finding_v1(finding_id: str, user: dict[str, Any] = Depends(get_current_user)):
        finding = store.get_finding(user["tenant_id"], finding_id)
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        finding["events"] = store.list_finding_events(user["tenant_id"], finding_id)
        finding["evidence"] = enrich_evidence(store.get_evidence(user["tenant_id"], finding.get("evidence_id")))
        return enrich_finding(finding)

    @app.post("/api/v1/findings/{finding_id}/acknowledge", tags=["inspection"])
    def acknowledge_finding_v1(
        finding_id: str,
        req: ActionRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        actor = get_actor(user, req.actor)
        finding = store.update_finding_action(
            user["tenant_id"],
            finding_id=finding_id,
            status_value="ACKNOWLEDGED",
            actor=actor,
            note=req.note,
        )
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        store.record_finding_event(
            user["tenant_id"],
            finding_id=finding_id,
            event_id=stable_id("event", finding_id, "ack", utc_now_iso(), actor),
            event_type="ACKNOWLEDGED",
            actor=actor,
            note=req.note,
            payload={},
        )
        return enrich_finding(finding)

    @app.post("/api/v1/findings/{finding_id}/assign", tags=["inspection"])
    def assign_finding_v1(
        finding_id: str,
        req: AssignRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        actor = get_actor(user, req.actor)
        finding = store.update_finding_action(
            user["tenant_id"],
            finding_id=finding_id,
            status_value="ASSIGNED",
            actor=actor,
            note=req.note,
            assigned_to=req.assignee,
        )
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        store.record_finding_event(
            user["tenant_id"],
            finding_id=finding_id,
            event_id=stable_id("event", finding_id, "assign", utc_now_iso(), actor),
            event_type="ASSIGNED",
            actor=actor,
            note=req.note,
            payload={"assignee": req.assignee},
        )
        return enrich_finding(finding)

    @app.post("/api/v1/findings/{finding_id}/reinspect", tags=["inspection"])
    def reinspect_finding_v1(
        finding_id: str,
        req: ReinspectRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        actor = get_actor(user, req.actor)
        finding = store.get_finding(user["tenant_id"], finding_id)
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        mission_id = stable_id("reinspect", finding_id, utc_now_iso(), actor)
        mission = store.upsert_mission(
            user["tenant_id"],
            {
                "mission_id": mission_id,
                "schema_version": "mission.v1",
                "site_id": finding["site_id"],
                "mission_profile": "operator_requested",
                "mission_type": "reinspection",
                "status": "QUEUED",
                "priority": req.priority,
                "selected_assets": [finding["asset_id"]],
                "follow_up_assets": [finding["asset_id"]],
                "linked_finding_id": finding_id,
                "requested_by": actor,
                "metadata": {
                    "reason": req.note or f"Reinspection requested for finding {finding_id}",
                    "source_finding_id": finding_id,
                    "source_checkpoint": finding["checkpoint_name"],
                },
            },
        )
        upsert_operator_queue_mission(
            settings.operator_queue_path,
            tenant_id=user["tenant_id"],
            mission={
                **mission,
                "mission_source": "operator_requested",
                "reason": req.note or f"Reinspection requested for finding {finding_id}",
            },
        )
        finding = store.update_finding_action(
            user["tenant_id"],
            finding_id=finding_id,
            status_value="REINSPECTION_REQUESTED",
            actor=actor,
            note=req.note,
        )
        store.record_finding_event(
            user["tenant_id"],
            finding_id=finding_id,
            event_id=stable_id("event", finding_id, "reinspect", utc_now_iso(), actor),
            event_type="REINSPECTION_REQUESTED",
            actor=actor,
            note=req.note,
            payload={"mission_id": mission_id, "priority": req.priority},
        )
        refresh_operator_state(user["tenant_id"])
        return {
            "finding": enrich_finding(finding),
            "linked_mission": store.get_mission(user["tenant_id"], mission_id),
        }

    @app.post("/api/v1/findings/{finding_id}/resolve", tags=["inspection"])
    def resolve_finding_v1(
        finding_id: str,
        req: ResolveRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        actor = get_actor(user, req.actor)
        finding = store.update_finding_action(
            user["tenant_id"],
            finding_id=finding_id,
            status_value="RESOLVED",
            actor=actor,
            note=req.resolution_note,
        )
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        store.record_finding_event(
            user["tenant_id"],
            finding_id=finding_id,
            event_id=stable_id("event", finding_id, "resolve", utc_now_iso(), actor),
            event_type="RESOLVED",
            actor=actor,
            note=req.resolution_note,
            payload={},
        )
        return enrich_finding(finding)

    @app.post("/api/v1/findings/{finding_id}/close", tags=["inspection"])
    def close_finding_v1(
        finding_id: str,
        req: ActionRequest,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        actor = get_actor(user, req.actor)
        finding = store.update_finding_action(
            user["tenant_id"],
            finding_id=finding_id,
            status_value="CLOSED",
            actor=actor,
            note=req.note,
        )
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        store.record_finding_event(
            user["tenant_id"],
            finding_id=finding_id,
            event_id=stable_id("event", finding_id, "close", utc_now_iso(), actor),
            event_type="CLOSED",
            actor=actor,
            note=req.note,
            payload={},
        )
        return enrich_finding(finding)

    @app.get("/api/v1/evidence/{evidence_id}", tags=["inspection"])
    def get_evidence_v1(evidence_id: str, user: dict[str, Any] = Depends(get_current_user)):
        evidence = store.get_evidence(user["tenant_id"], evidence_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="Evidence not found")
        return enrich_evidence(evidence)

    @app.get("/api/v1/evidence/{evidence_id}/primary", tags=["inspection"])
    def get_evidence_primary_v1(
        evidence_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        return serve_evidence_variant(user["tenant_id"], evidence_id, "primary")

    @app.get("/api/v1/evidence/{evidence_id}/annotated", tags=["inspection"])
    def get_evidence_annotated_v1(
        evidence_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        return serve_evidence_variant(user["tenant_id"], evidence_id, "annotated")

    @app.get("/api/v1/evidence/{evidence_id}/raw", tags=["inspection"])
    def get_evidence_raw_v1(
        evidence_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        return serve_evidence_variant(user["tenant_id"], evidence_id, "raw")

    @app.get("/api/v1/evidence/by-asset/{asset_id}/annotated", tags=["inspection"])
    def get_latest_asset_image_v1(
        asset_id: str,
        user: dict[str, Any] = Depends(get_current_user),
    ):
        asset = store.get_asset(user["tenant_id"], asset_id)
        if asset is None or not asset.get("latest_annotated_image_path"):
            raise HTTPException(status_code=404, detail="No annotated image recorded for this asset")
        image_path = Path(asset["latest_annotated_image_path"])
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Annotated image file is missing on disk")
        return FileResponse(image_path)

    @app.get("/api/v1/health", tags=["system"])
    def health_v1(user: dict[str, Any] = Depends(get_current_user)):
        try:
            with store.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            database_status = "pass"
        except Exception:
            database_status = "fail"
        influx_status = influx_handles.status
        latest_sync = store.get_latest_sync_run(user["tenant_id"])
        return {
            "status": "ok" if database_status == "pass" else "degraded",
            "database": database_status,
            "influx": influx_status,
            "version": settings.app_version,
            "benchmark_runtime_root": str(settings.runtime_root),
            "site_config_file": str(settings.site_config_path),
            "asset_registry_file": str(settings.asset_registry_path),
            "inspection_profiles_file": str(settings.inspection_profiles_path),
            "latest_sync": latest_sync,
            "timestamp": utc_now_iso(),
        }

    @app.get("/health", tags=["system"])
    def health_compat():
        try:
            with store.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            database_status = "pass"
        except Exception:
            database_status = "fail"
        return {
            "status": "ok" if database_status == "pass" else "degraded",
            "database": database_status,
            "influx": influx_handles.status,
            "version": settings.app_version,
            "timestamp": utc_now_iso(),
        }

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(settings.ui_path)

    @app.get("/ui", include_in_schema=False)
    def dashboard_alias():
        return FileResponse(settings.ui_path)

    return app


app = create_app()
