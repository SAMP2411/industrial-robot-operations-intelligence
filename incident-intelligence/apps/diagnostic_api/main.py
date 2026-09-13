from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
import hashlib
import os
import shutil
import tempfile
import zipfile
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session
import yaml

from packages.audit import audit
from packages.common import Settings, get_settings
from packages.domain_models.database import create_schema, get_session
from packages.domain_models.models import (
    Asset,
    AssetDependency,
    AssetMappingDecision,
    AuditEvent,
    CorrectiveAction,
    Customer,
    DataSource,
    DataQualityIssue,
    DiagnosticEngagement,
    DeletionRequest,
    DatasetRegistration,
    DowntimeSegment,
    EvidenceLink,
    EventGroup,
    Incident,
    IncidentLifecycleMarker,
    IncidentSuggestion,
    HypothesisReview,
    IngestionRun,
    Job,
    JobAttempt,
    JobEvent,
    ImportEffortRecord,
    MappingProfileVersion,
    RawRecord,
    RedactionAudit,
    RecoveryAction,
    RecoveryMilestone,
    ReportArtifact,
    RootCauseHypothesis,
    Site,
    System,
    User,
    ValidationDecision,
    ValidationRecord,
)
from packages.ingestion_core import IngestionService
from packages.ingestion_core.archive import extract_safe_zip
from packages.job_queue import DurableJobQueue
from packages.data_quality import assess_incident
from packages.hypothesis_engine import recalculate_confidence
from packages.incident_engine import calculate_metrics, create_downtime_segment, create_recovery_action
from packages.incident_analysis import compare_incidents, dependency_impact, recurring_matches, suggest_incident_windows
from packages.report_generation import approve_report_version, generate_report_bundle
from packages.report_generation.redaction import redact
from packages.retention import approve_deletion, execute_deletion, preview_deletion
from packages.timeline_engine import TimelineFilters, add_annotation, build_timeline, update_clock_offset
from packages.common.security import decode_token, hash_password, issue_token, new_reset_token, verify_password
from packages.common.observability import prometheus_text, request_observability
import packages.common.observability as observability

from .schemas import (
    AnnotationCreate, ApprovalCreate, AssetCreate, AssetDependencyCreate, AssetMappingDecisionCreate, BoundaryUpdate, ClockOffsetUpdate, CorrectiveActionCreate, CustomerCreate,
    DataSourceCreate, DowntimeCreate, EngagementCreate, EvidenceCreate, HypothesisCreate,
    HypothesisStatusPatch, IncidentCreate, IncidentPatch, RecoveryCreate, ReportCreate,
    SiteCreate, SystemCreate,
    UserCreate, LoginRequest, PasswordResetRequest, PasswordResetConfirm,
    ValidationDecisionCreate, ValidationRecordCreate, MappingProfileCreate, JobCreate,
    LifecycleMarkerCreate, RecoveryMilestoneCreate, EventGroupCreate,
    EvidenceReviewCreate, HypothesisReviewCreate,
    RedactionPreviewCreate,
    DeletionPreviewCreate,
    DatasetRegistrationCreate, ImportEffortCreate,
)


ROLE_PERMISSIONS = {
    "admin": {"read", "write", "upload", "approve", "admin"},
    "analyst": {"read", "write", "upload"},
    "reviewer": {"read", "approve"},
    "operator": {"read", "write"},
    "partner": {"read", "upload"},
    "viewer": {"read"},
}
LOGIN_ATTEMPTS: dict[str, deque] = defaultdict(deque)


def enforce_login_rate_limit(key: str, limit: int, window_seconds: int = 300) -> None:
    now = datetime.now(timezone.utc).timestamp()
    attempts = LOGIN_ATTEMPTS[key]
    while attempts and attempts[0] < now - window_seconds: attempts.popleft()
    if len(attempts) >= limit:
        raise HTTPException(status_code=429, detail={"code": "login_rate_limited", "retry_after_seconds": window_seconds})
    attempts.append(now)


def actor_header(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_actor: Annotated[str | None, Header()] = None,
    x_customer_id: Annotated[str | None, Header(alias="X-Customer-ID")] = None,
    session: Session = Depends(get_session),
) -> str:
    settings = request.app.state.settings
    if not settings.auth_required:
        request.state.principal = {"user_id": x_actor or "local-analyst", "customer_id": x_customer_id, "role": request.headers.get("X-Role", "analyst")}
        return x_actor or "local-analyst"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "authentication_required"})
    try:
        payload = decode_token(authorization[7:], secret_key=settings.secret_key)
        user = session.get(User, payload["sub"])
        if user is None or user.disabled or user.token_version != payload["ver"]:
            raise ValueError
        request.state.principal = {"user_id": user.id, "customer_id": user.customer_id, "role": user.role_name}
        return user.email
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=401, detail={"code": "invalid_token"}) from exc


def require_permission(permission: str):
    def dependency(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
        x_role: Annotated[str | None, Header()] = None,
        x_customer_id: Annotated[str | None, Header(alias="X-Customer-ID")] = None,
        session: Session = Depends(get_session),
    ) -> str:
        settings = request.app.state.settings
        role = x_role or "analyst"
        if settings.auth_required:
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail={"code": "authentication_required"})
            try:
                payload = decode_token(authorization[7:], secret_key=settings.secret_key)
                user = session.get(User, payload["sub"])
                if user is None or user.disabled or user.token_version != payload["ver"]:
                    raise ValueError("account disabled or token revoked")
                role = user.role_name
                request.state.principal = {"user_id": user.id, "customer_id": user.customer_id, "role": role}
            except (ValueError, KeyError) as exc:
                raise HTTPException(status_code=401, detail={"code": "invalid_token"}) from exc
        if role not in ROLE_PERMISSIONS or permission not in ROLE_PERMISSIONS[role]:
            raise HTTPException(status_code=403, detail={"code": "permission_denied", "required": permission})
        if not settings.auth_required:
            request.state.principal = {"user_id": request.headers.get("X-Actor", "local-analyst"), "customer_id": x_customer_id, "role": role}
        scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped:
            path_models = {
                "incident_id": Incident, "engagement_id": DiagnosticEngagement, "source_id": DataSource,
                "run_id": IngestionRun, "raw_record_id": RawRecord, "artifact_id": ReportArtifact,
                "asset_id": Asset, "site_id": Site, "registration_id": DatasetRegistration,
            }
            for parameter, model in path_models.items():
                entity_id = request.path_params.get(parameter)
                if entity_id:
                    entity = session.get(model, entity_id)
                    if entity and entity_customer_id(session, entity) != scoped:
                        raise HTTPException(status_code=404, detail={"code": "not_found"})
        return role
    return dependency


def entity_dict(entity: Any) -> dict[str, Any]:
    return {column.name: getattr(entity, column.name) for column in entity.__table__.columns}


def get_or_404(session: Session, model, entity_id: str):
    entity = session.get(model, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "entity": model.__name__})
    return entity


def enforce_customer_scope(request: Request, customer_id: str) -> None:
    scoped = getattr(request.state, "principal", {}).get("customer_id")
    if scoped and scoped != customer_id:
        raise HTTPException(status_code=404, detail={"code": "not_found"})


def entity_customer_id(session: Session, entity: Any) -> str | None:
    if isinstance(entity, Customer): return entity.id
    if isinstance(entity, Site): return entity.customer_id
    if isinstance(entity, (System, Asset)): return session.get(Site, entity.site_id).customer_id
    if isinstance(entity, DiagnosticEngagement): return entity.customer_id
    if isinstance(entity, DataSource): return session.get(DiagnosticEngagement, entity.engagement_id).customer_id
    if isinstance(entity, IngestionRun): return entity_customer_id(session, session.get(DataSource, entity.data_source_id))
    if isinstance(entity, RawRecord): return entity_customer_id(session, session.get(DataSource, entity.data_source_id))
    if isinstance(entity, Incident): return entity_customer_id(session, session.get(DiagnosticEngagement, entity.diagnostic_engagement_id))
    if isinstance(entity, ReportArtifact): return entity_customer_id(session, session.get(Incident, entity.incident_id))
    if isinstance(entity, DatasetRegistration): return entity.customer_id
    return None


def scoped_entity(request: Request, session: Session, model, entity_id: str):
    entity = get_or_404(session, model, entity_id)
    customer_id = entity_customer_id(session, entity)
    if customer_id: enforce_customer_scope(request, customer_id)
    return entity


async def stage_upload(file: UploadFile, staging_root: Path, max_bytes: int) -> tuple[Path, int, str]:
    """Stream an HTTP upload to a bounded temporary file with an incremental digest."""
    staging_root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    handle = tempfile.NamedTemporaryFile(prefix="upload-", suffix=".partial", dir=staging_root, delete=False)
    path = Path(handle.name)
    try:
        with handle:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("upload exceeds configured size limit")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
        return path, size, digest.hexdigest()
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def create_app(settings: Settings | None = None, *, initialize_schema: bool = True) -> FastAPI:
    settings = settings or get_settings()
    if initialize_schema:
        create_schema()
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    settings.report_root.mkdir(parents=True, exist_ok=True)
    app = FastAPI(
        title="Robot Fleet Incident Intelligence API",
        version="0.1.0",
        description="Read-only evidence ingestion and historical incident reconstruction. This API never controls robots or production systems.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Actor", "X-Role", "X-Customer-ID", "X-Request-ID"],
    )
    app.middleware("http")(request_observability)
    app.state.settings = settings

    def ingestion_service(session: Session) -> IngestionService:
        return IngestionService(
            session, settings.upload_root, settings.max_upload_bytes,
            encryption_key=settings.evidence_encryption_key,
            encryption_key_id=settings.evidence_encryption_key_id,
        )

    @app.get("/health")
    def health(session: Session = Depends(get_session)):
        session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "storage": settings.storage_root.exists(), "schema_version": "1.0"}

    @app.get("/metrics", response_class=Response, dependencies=[Depends(require_permission("admin"))])
    def operational_metrics(session: Session = Depends(get_session)):
        active = len(session.scalars(select(Job).where(Job.status.in_(("queued", "running", "retrying")))).all())
        failed = len(session.scalars(select(Job).where(Job.status == "failed")).all())
        storage_bytes = sum(path.stat().st_size for path in settings.storage_root.rglob("*") if path.is_file())
        return Response(prometheus_text(active_jobs=active, failed_jobs=failed, storage_bytes=storage_bytes), media_type="text/plain; version=0.0.4")

    @app.get("/", response_class=HTMLResponse)
    def console():
        ui_path = Path(__file__).resolve().parents[1] / "operator_console" / "index.html"
        return ui_path.read_text() if ui_path.exists() else "<h1>Incident Console</h1>"

    @app.post("/auth/users", dependencies=[Depends(require_permission("admin"))])
    def create_user(payload: UserCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        if session.scalar(select(User).where(User.email == payload.email.lower())):
            raise HTTPException(status_code=409, detail={"code": "email_exists"})
        try:
            password_hash = hash_password(payload.password)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "weak_password", "message": str(exc)}) from exc
        user = User(email=payload.email.lower(), password_hash=password_hash, role_name=payload.role_name, customer_id=payload.customer_id)
        session.add(user); session.flush(); audit(session, actor=actor, action="user_create", entity_type="user", entity_id=user.id, details={"role": user.role_name}); session.commit()
        return {"id": user.id, "email": user.email, "role_name": user.role_name, "schema_version": "1.0"}

    @app.post("/auth/users/{user_id}/disable", dependencies=[Depends(require_permission("admin"))])
    def disable_user(user_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        user = get_or_404(session, User, user_id)
        user.disabled = True; user.token_version += 1
        audit(session, actor=actor, action="account_disable", entity_type="user", entity_id=user.id); session.commit()
        return {"id": user.id, "disabled": True, "schema_version": "1.0"}

    @app.post("/auth/token")
    def login(payload: LoginRequest, request: Request, session: Session = Depends(get_session)):
        rate_key = f"{request.client.host if request.client else 'unknown'}:{payload.email.casefold()}"
        enforce_login_rate_limit(rate_key, settings.login_attempt_limit)
        user = session.scalar(select(User).where(User.email == payload.email.lower()))
        if user is None or user.disabled or not verify_password(payload.password, user.password_hash):
            observability.LOGIN_FAILURES += 1
            audit(session, actor=payload.email.lower(), action="login_failed", entity_type="user", entity_id=user.id if user else None, details={"remote": request.client.host if request.client else None}); session.commit()
            raise HTTPException(status_code=401, detail={"code": "invalid_credentials"})
        LOGIN_ATTEMPTS.pop(rate_key, None)
        token = issue_token(user_id=user.id, role=user.role_name, token_version=user.token_version, secret_key=settings.secret_key, expire_minutes=settings.token_expire_minutes)
        audit(session, actor=user.email, action="login", entity_type="user", entity_id=user.id); session.commit()
        return {"access_token": token, "token_type": "bearer", "expires_in": settings.token_expire_minutes * 60}

    @app.post("/auth/password-reset/request")
    def request_password_reset(payload: PasswordResetRequest, session: Session = Depends(get_session)):
        user = session.scalar(select(User).where(User.email == payload.email.lower()))
        response = {"status": "accepted"}
        if user:
            token, digest = new_reset_token()
            user.reset_token_hash = digest
            user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=20)
            audit(session, actor=user.email, action="password_reset_requested", entity_type="user", entity_id=user.id); session.commit()
            if settings.app_env == "development": response["development_reset_token"] = token
        return response

    @app.post("/auth/password-reset/confirm")
    def confirm_password_reset(payload: PasswordResetConfirm, session: Session = Depends(get_session)):
        digest = hashlib.sha256(payload.token.encode()).hexdigest()
        user = session.scalar(select(User).where(User.reset_token_hash == digest))
        now = datetime.now(timezone.utc)
        expires = user.reset_token_expires_at if user else None
        if expires and expires.tzinfo is None: expires = expires.replace(tzinfo=timezone.utc)
        if user is None or not expires or expires < now:
            raise HTTPException(status_code=400, detail={"code": "invalid_or_expired_reset_token"})
        user.password_hash = hash_password(payload.new_password); user.reset_token_hash = None; user.reset_token_expires_at = None; user.token_version += 1
        audit(session, actor=user.email, action="password_reset", entity_type="user", entity_id=user.id); session.commit()
        return {"status": "password_updated"}

    @app.post("/api/v1/customers", dependencies=[Depends(require_permission("write"))])
    def create_customer(payload: CustomerCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = Customer(name=payload.name)
        session.add(entity); session.flush()
        audit(session, actor=actor, action="customer_create", entity_type="customer", entity_id=entity.id)
        session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/customers", dependencies=[Depends(require_permission("read"))])
    def list_customers(request: Request, session: Session = Depends(get_session)):
        query = select(Customer).order_by(Customer.name)
        scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped: query = query.where(Customer.id == scoped)
        rows = session.scalars(query).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/sites", dependencies=[Depends(require_permission("write"))])
    def create_site(payload: SiteCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Customer, payload.customer_id)
        enforce_customer_scope(request, payload.customer_id)
        entity = Site(**payload.model_dump())
        session.add(entity); session.flush(); audit(session, actor=actor, action="site_create", entity_type="site", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/sites", dependencies=[Depends(require_permission("read"))])
    def list_sites(request: Request, session: Session = Depends(get_session)):
        query = select(Site).order_by(Site.name); scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped: query = query.where(Site.customer_id == scoped)
        return {"items": [entity_dict(row) for row in session.scalars(query).all()], "schema_version": "1.0"}

    @app.post("/api/v1/systems", dependencies=[Depends(require_permission("write"))])
    def create_system(payload: SystemCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        scoped_entity(request, session, Site, payload.site_id)
        entity = System(**payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="system_create", entity_type="system", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/systems", dependencies=[Depends(require_permission("read"))])
    def list_systems(request: Request, site_id: str | None = None, session: Session = Depends(get_session)):
        query = select(System).order_by(System.name)
        if site_id: query = query.where(System.site_id == site_id)
        rows = session.scalars(query).all(); rows = [row for row in rows if not getattr(request.state, "principal", {}).get("customer_id") or entity_customer_id(session, row) == request.state.principal["customer_id"]]
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/assets", dependencies=[Depends(require_permission("write"))])
    def create_asset(payload: AssetCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        scoped_entity(request, session, Site, payload.site_id)
        values = payload.model_dump(); values["metadata_json"] = values.pop("metadata")
        entity = Asset(**values); session.add(entity); session.flush(); audit(session, actor=actor, action="asset_create", entity_type="asset", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.patch("/api/v1/assets/{asset_id}/aliases", dependencies=[Depends(require_permission("write"))])
    def add_asset_alias(asset_id: str, alias: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = get_or_404(session, Asset, asset_id)
        entity.aliases = sorted(set([*(entity.aliases or []), alias]))
        audit(session, actor=actor, action="asset_alias_change", entity_type="asset", entity_id=entity.id, details={"alias": alias}); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/assets", dependencies=[Depends(require_permission("read"))])
    def list_assets(request: Request, site_id: str | None = None, session: Session = Depends(get_session)):
        query = select(Asset).order_by(Asset.name)
        if site_id: query = query.where(Asset.site_id == site_id)
        rows = session.scalars(query).all(); rows = [row for row in rows if not getattr(request.state, "principal", {}).get("customer_id") or entity_customer_id(session, row) == request.state.principal["customer_id"]]
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.get("/api/v1/assets/{asset_id}/dependencies", dependencies=[Depends(require_permission("read"))])
    def dependencies(asset_id: str, session: Session = Depends(get_session)):
        get_or_404(session, Asset, asset_id)
        rows = session.scalars(select(AssetDependency).where((AssetDependency.source_asset_id == asset_id) | (AssetDependency.target_asset_id == asset_id))).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/asset-dependencies", dependencies=[Depends(require_permission("write"))])
    def create_dependency(payload: AssetDependencyCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Asset, payload.source_asset_id); get_or_404(session, Asset, payload.target_asset_id)
        entity = AssetDependency(**payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="asset_dependency_create", entity_type="asset_dependency", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.post("/api/v1/sites/{site_id}/asset-registry/import", dependencies=[Depends(require_permission("upload"))])
    async def import_asset_registry(site_id: str, file: UploadFile = File(...), actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Site, site_id)
        content = await file.read(settings.max_upload_bytes + 1)
        try:
            document = yaml.safe_load(content)
            rows = document.get("assets", [])
            if not isinstance(rows, list): raise ValueError("assets must be a list")
        except (yaml.YAMLError, ValueError, AttributeError) as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_asset_registry", "message": str(exc)}) from exc
        imported = 0
        for row in rows:
            external_id = str(row.get("asset_id", ""))
            if not external_id: continue
            existing = session.scalar(select(Asset).where(Asset.site_id == site_id, Asset.external_asset_id == external_id))
            values = {
                "site_id": site_id, "name": str(row.get("name", external_id)), "asset_type": str(row.get("asset_type", "unknown")),
                "external_asset_id": external_id, "aliases": list(row.get("aliases", [])),
                "metadata_json": {key: value for key, value in row.items() if key not in {"name", "asset_type", "asset_id", "aliases"}},
            }
            if existing:
                for key, value in values.items(): setattr(existing, key, value)
            else:
                session.add(Asset(**values))
            imported += 1
        audit(session, actor=actor, action="asset_registry_import", entity_type="site", entity_id=site_id, details={"assets_imported": imported, "schema_version": document.get("schema_version")}); session.commit()
        return {"assets_imported": imported, "schema_version": "1.0"}

    @app.post("/api/v1/diagnostic-engagements", dependencies=[Depends(require_permission("write"))])
    def create_engagement(payload: EngagementCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        enforce_customer_scope(request, payload.customer_id)
        get_or_404(session, Customer, payload.customer_id); get_or_404(session, Site, payload.site_id)
        entity = DiagnosticEngagement(**payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="engagement_create", entity_type="diagnostic_engagement", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/diagnostic-engagements", dependencies=[Depends(require_permission("read"))])
    def list_engagements(request: Request, session: Session = Depends(get_session)):
        query = select(DiagnosticEngagement).order_by(DiagnosticEngagement.created_at.desc()); scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped: query = query.where(DiagnosticEngagement.customer_id == scoped)
        return {"items": [entity_dict(row) for row in session.scalars(query).all()], "schema_version": "1.0"}

    @app.post("/api/v1/diagnostic-engagements/{engagement_id}/sources", dependencies=[Depends(require_permission("write"))])
    def create_source(engagement_id: str, payload: DataSourceCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        scoped_entity(request, session, DiagnosticEngagement, engagement_id)
        entity = DataSource(engagement_id=engagement_id, **payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="data_source_create", entity_type="data_source", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/diagnostic-engagements/{engagement_id}/sources", dependencies=[Depends(require_permission("read"))])
    def list_sources(engagement_id: str, request: Request, session: Session = Depends(get_session)):
        scoped_entity(request, session, DiagnosticEngagement, engagement_id)
        rows = session.scalars(select(DataSource).where(DataSource.engagement_id == engagement_id).order_by(DataSource.name)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/asset-mappings", dependencies=[Depends(require_permission("write"))])
    def create_asset_mapping(payload: AssetMappingDecisionCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, DiagnosticEngagement, payload.engagement_id)
        if payload.asset_id: get_or_404(session, Asset, payload.asset_id)
        if payload.system_id: get_or_404(session, System, payload.system_id)
        if payload.target_type == "asset" and not payload.asset_id:
            raise HTTPException(status_code=422, detail={"code": "asset_id_required"})
        entity = AssetMappingDecision(created_by=actor, **payload.model_dump())
        session.add(entity); session.flush()
        if entity.asset_id and entity.match_method in {"alias", "analyst_confirmation"}:
            asset = session.get(Asset, entity.asset_id)
            asset.aliases = sorted(set([*(asset.aliases or []), entity.external_identifier]))
        audit(session, actor=actor, action="asset_mapping", entity_type="asset_mapping_decision", entity_id=entity.id, details={"external_identifier": entity.external_identifier, "rationale": entity.rationale}); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/diagnostic-engagements/{engagement_id}/asset-mappings", dependencies=[Depends(require_permission("read"))])
    def list_asset_mappings(engagement_id: str, session: Session = Depends(get_session)):
        rows = session.scalars(select(AssetMappingDecision).where(AssetMappingDecision.engagement_id == engagement_id).order_by(AssetMappingDecision.created_at.desc())).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/diagnostic-engagements/{engagement_id}/bundles", dependencies=[Depends(require_permission("upload"))])
    async def upload_evidence_bundle(
        engagement_id: str,
        file: UploadFile = File(...),
        actor: str = Depends(actor_header),
        session: Session = Depends(get_session),
    ):
        get_or_404(session, DiagnosticEngagement, engagement_id)
        if Path(file.filename or "").suffix.lower() != ".zip":
            raise HTTPException(status_code=422, detail={"code": "zip_required"})
        staged_path: Path | None = None
        try:
            staged_path, size_bytes, digest = await stage_upload(file, settings.upload_root / ".staging", settings.max_upload_bytes)
            bundle_root = settings.upload_root / "bundles" / engagement_id / digest
            original = bundle_root / "original.zip"
            extracted = bundle_root / "extracted"
            bundle_root.mkdir(parents=True, exist_ok=True)
            temporary = bundle_root / "original.zip.partial"
            shutil.copyfile(staged_path, temporary)
            os.replace(temporary, original)
            manifest = extract_safe_zip(original, extracted, max_uncompressed_bytes=settings.max_upload_bytes * 10)
            audit(session, actor=actor, action="evidence_bundle_upload", entity_type="diagnostic_engagement", entity_id=engagement_id, details={"sha256": digest, "size_bytes": size_bytes, "files": len(manifest["files"])})
            session.commit()
            return {**manifest, "size_bytes": size_bytes, "schema_version": "1.0"}
        except (ValueError, OSError, zipfile.BadZipFile) as exc:
            if 'bundle_root' in locals(): shutil.rmtree(bundle_root, ignore_errors=True)
            raise HTTPException(status_code=422, detail={"code": "invalid_bundle", "message": str(exc)}) from exc
        finally:
            if staged_path: staged_path.unlink(missing_ok=True)

    @app.post("/api/v1/mapping-profiles", dependencies=[Depends(require_permission("write"))])
    def create_mapping_profile(payload: MappingProfileCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        if session.scalar(select(MappingProfileVersion).where(MappingProfileVersion.name == payload.name, MappingProfileVersion.version == payload.version)):
            raise HTTPException(status_code=409, detail={"code": "profile_version_exists"})
        entity = MappingProfileVersion(author=actor, **payload.model_dump())
        session.add(entity); session.flush()
        audit(session, actor=actor, action="mapping_profile_create", entity_type="mapping_profile_version", entity_id=entity.id, details={"name": entity.name, "version": entity.version})
        session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/mapping-profiles", dependencies=[Depends(require_permission("read"))])
    def list_mapping_profiles(source_type: str | None = None, session: Session = Depends(get_session)):
        query = select(MappingProfileVersion).order_by(MappingProfileVersion.name, MappingProfileVersion.created_at.desc())
        if source_type: query = query.where(MappingProfileVersion.source_type == source_type)
        return {"items": [entity_dict(row) for row in session.scalars(query).all()], "schema_version": "1.0"}

    @app.post("/api/v1/jobs", dependencies=[Depends(require_permission("write"))])
    def enqueue_job(payload: JobCreate, request: Request, session: Session = Depends(get_session)):
        customer_id = getattr(request.state, "principal", {}).get("customer_id")
        job = DurableJobQueue(session).enqueue(payload.job_type, payload.payload, payload.idempotency_key, payload.max_retries, customer_id=customer_id)
        item = entity_dict(job); item.pop("error_details", None)
        return item

    @app.get("/api/v1/jobs/{job_id}", dependencies=[Depends(require_permission("read"))])
    def job_status(job_id: str, session: Session = Depends(get_session)):
        job = get_or_404(session, Job, job_id)
        item = entity_dict(job); item.pop("error_details", None)
        events = session.scalars(select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)).all()
        return {**item, "events": [entity_dict(event) for event in events]}

    @app.get("/api/v1/admin/jobs/{job_id}", dependencies=[Depends(require_permission("admin"))])
    def admin_job_status(job_id: str, session: Session = Depends(get_session)):
        job = get_or_404(session, Job, job_id)
        attempts = session.scalars(select(JobAttempt).where(JobAttempt.job_id == job_id).order_by(JobAttempt.created_at)).all()
        return {**entity_dict(job), "attempts": [entity_dict(item) for item in attempts]}

    @app.post("/api/v1/sources/{source_id}/uploads/preview", dependencies=[Depends(require_permission("upload"))])
    async def preview_upload(
        source_id: str,
        file: UploadFile = File(...),
        mapping_yaml: str = Form(""),
        encoding: str | None = Form(None),
        session: Session = Depends(get_session),
    ):
        get_or_404(session, DataSource, source_id)
        staged_path: Path | None = None
        try:
            staged_path, _, _ = await stage_upload(file, settings.upload_root / ".staging", settings.max_upload_bytes)
            mapping = yaml.safe_load(mapping_yaml) if mapping_yaml else {}
            preview = ingestion_service(session).preview_path(
                filename=file.filename or "", path=staged_path, mapping=mapping, encoding=encoding
            )
        except (ValueError, UnicodeDecodeError, yaml.YAMLError) as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_upload", "message": str(exc)}) from exc
        finally:
            if staged_path: staged_path.unlink(missing_ok=True)
        return {**asdict(preview), "schema_version": "1.0"}

    @app.post("/api/v1/sources/{source_id}/uploads", dependencies=[Depends(require_permission("upload"))])
    async def upload(
        source_id: str,
        file: UploadFile = File(...),
        mapping_yaml: str = Form(""),
        encoding: str | None = Form(None),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
        actor: str = Depends(actor_header),
        session: Session = Depends(get_session),
    ):
        get_or_404(session, DataSource, source_id)
        staged_path: Path | None = None
        try:
            staged_path, size_bytes, digest = await stage_upload(file, settings.upload_root / ".staging", settings.max_upload_bytes)
            mapping = yaml.safe_load(mapping_yaml) if mapping_yaml else {}
            run = ingestion_service(session).create_run_from_staged(
                data_source_id=source_id, filename=file.filename or "", staged_path=staged_path,
                size_bytes=size_bytes, digest=digest,
                mime_type=file.content_type or "application/octet-stream", mapping=mapping,
                idempotency_key=idempotency_key, actor=actor, encoding=encoding,
            )
        except (ValueError, UnicodeDecodeError, yaml.YAMLError) as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_upload", "message": str(exc)}) from exc
        finally:
            if staged_path: staged_path.unlink(missing_ok=True)
        result = entity_dict(run); result.pop("storage_path", None)
        return result

    @app.post("/api/v1/ingestion-runs/{run_id}/preview", dependencies=[Depends(require_permission("read"))])
    def preview_run(run_id: str, session: Session = Depends(get_session)):
        run = get_or_404(session, IngestionRun, run_id)
        service = ingestion_service(session)
        with service.preserved_path(run) as path:
            preview = service.preview_path(filename=run.source_filename, path=path, mapping=run.mapping_profile, encoding=run.selected_encoding)
        return {**asdict(preview), "schema_version": "1.0"}

    @app.post("/api/v1/ingestion-runs/{run_id}/commit", dependencies=[Depends(require_permission("write"))])
    def commit_run(run_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        try:
            summary = ingestion_service(session).commit(run_id, actor=actor)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "not_found", "entity": "IngestionRun"}) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "ingestion_conflict", "message": str(exc)}) from exc
        return {**summary, "schema_version": "1.0"}

    @app.get("/api/v1/ingestion-runs/{run_id}/summary", dependencies=[Depends(require_permission("read"))])
    def run_summary(run_id: str, session: Session = Depends(get_session)):
        run = get_or_404(session, IngestionRun, run_id)
        return {**(run.summary or {}), "status": run.status, "schema_version": "1.0"}

    @app.get("/api/v1/data-sources/{source_id}/ingestion-runs", dependencies=[Depends(require_permission("read"))])
    def list_ingestion_runs(source_id: str, session: Session = Depends(get_session)):
        get_or_404(session, DataSource, source_id)
        rows = session.scalars(select(IngestionRun).where(IngestionRun.data_source_id == source_id).order_by(IngestionRun.created_at.desc())).all()
        items = []
        for row in rows:
            item = entity_dict(row); item.pop("storage_path", None); items.append(item)
        return {"items": items, "schema_version": "1.0"}

    @app.get("/api/v1/raw-records/{raw_record_id}", dependencies=[Depends(require_permission("read"))])
    def raw_record(raw_record_id: str, request: Request, session: Session = Depends(get_session)):
        raw = scoped_entity(request, session, RawRecord, raw_record_id)
        return {
            "id": raw.id, "ingestion_run_id": raw.ingestion_run_id, "data_source_id": raw.data_source_id,
            "source_record_id": raw.source_record_id, "source_filename": raw.source_filename,
            "source_line_number": raw.source_line_number, "source_timestamp_raw": raw.source_timestamp_raw,
            "payload": raw.payload, "payload_sha256": raw.payload_sha256, "ingested_at": raw.ingested_at,
            "schema_version": raw.schema_version,
        }

    @app.post("/api/v1/incidents", dependencies=[Depends(require_permission("write"))])
    def create_incident(payload: IncidentCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        engagement = scoped_entity(request, session, DiagnosticEngagement, payload.diagnostic_engagement_id)
        site = scoped_entity(request, session, Site, payload.site_id)
        if engagement.site_id != site.id: raise HTTPException(status_code=409, detail={"code": "site_not_in_engagement"})
        values = payload.model_dump(); values["created_by"] = actor
        entity = Incident(**values); session.add(entity); session.flush(); audit(session, actor=actor, action="incident_create", entity_type="incident", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents", dependencies=[Depends(require_permission("read"))])
    def list_incidents(request: Request, status: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
        query = select(Incident).order_by(Incident.started_at.desc()).limit(limit).offset(offset)
        if status: query = query.where(Incident.status == status)
        rows = session.scalars(query).all(); rows = [row for row in rows if not getattr(request.state, "principal", {}).get("customer_id") or entity_customer_id(session, row) == request.state.principal["customer_id"]]
        return {"items": [entity_dict(row) for row in rows], "limit": limit, "offset": offset, "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}", dependencies=[Depends(require_permission("read"))])
    def get_incident(incident_id: str, request: Request, session: Session = Depends(get_session)):
        return entity_dict(scoped_entity(request, session, Incident, incident_id))

    @app.patch("/api/v1/incidents/{incident_id}", dependencies=[Depends(require_permission("write"))])
    def patch_incident(incident_id: str, payload: IncidentPatch, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = scoped_entity(request, session, Incident, incident_id)
        for key, value in payload.model_dump(exclude_unset=True).items(): setattr(entity, key, value)
        audit(session, actor=actor, action="incident_change", entity_type="incident", entity_id=entity.id, details=payload.model_dump(exclude_unset=True, mode="json")); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents/{incident_id}/timeline", dependencies=[Depends(require_permission("read"))])
    def timeline(
        incident_id: str,
        source_id: str | None = None,
        system_id: str | None = None,
        asset_id: str | None = None,
        severity: str | None = None,
        event_type: str | None = None,
        session: Session = Depends(get_session),
    ):
        incident = get_or_404(session, Incident, incident_id)
        items = build_timeline(session, incident, TimelineFilters(source_id, system_id, asset_id, severity, event_type))
        return {"items": items, "count": len(items), "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/timeline/export", dependencies=[Depends(require_permission("read"))])
    def timeline_export(incident_id: str, session: Session = Depends(get_session)):
        import csv
        import io
        incident = get_or_404(session, Incident, incident_id)
        items = build_timeline(session, incident, TimelineFilters())
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["occurred_at", "entry_type", "source", "asset_id", "severity", "event_code", "message", "raw_record_id"])
        for item in items:
            writer.writerow([item.get("occurred_at"), item.get("entry_type"), (item.get("source") or {}).get("name"), item.get("asset_id"), item.get("severity"), item.get("event_code"), item.get("message", item.get("annotation")), (item.get("raw_evidence") or {}).get("raw_record_id")])
        return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="incident-{incident_id}-timeline.csv"'})

    @app.post("/api/v1/incidents/{incident_id}/timeline/annotations", dependencies=[Depends(require_permission("write"))])
    def timeline_annotation(incident_id: str, payload: AnnotationCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        return entity_dict(add_annotation(session, incident_id, **payload.model_dump(), actor=actor))

    @app.post("/api/v1/incidents/{incident_id}/clock-offsets", dependencies=[Depends(require_permission("write"))])
    def clock_offset(incident_id: str, payload: ClockOffsetUpdate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        source = get_or_404(session, DataSource, payload.data_source_id)
        if source.engagement_id != incident.diagnostic_engagement_id:
            raise HTTPException(status_code=409, detail={"code": "source_not_in_incident_engagement"})
        updated = update_clock_offset(
            session, source.id, payload.clock_offset_ms, reason=payload.reason, actor=actor,
            uncertainty_ms=payload.uncertainty_ms, method=payload.method, evidence_links=payload.evidence_links,
        )
        return {"data_source_id": source.id, "clock_offset_ms": payload.clock_offset_ms, "events_updated": updated, "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/timeline/boundaries", dependencies=[Depends(require_permission("write"))])
    def timeline_boundaries(incident_id: str, payload: BoundaryUpdate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        if payload.recovered_at and payload.recovered_at < payload.started_at:
            raise HTTPException(status_code=422, detail={"code": "invalid_incident_boundaries"})
        incident.started_at = payload.started_at; incident.recovered_at = payload.recovered_at
        audit(session, actor=actor, action="incident_boundary_change", entity_type="incident", entity_id=incident.id, details=payload.model_dump(mode="json")); session.commit()
        return entity_dict(incident)

    @app.post("/api/v1/incidents/{incident_id}/downtime-segments", dependencies=[Depends(require_permission("write"))])
    def downtime_segment(incident_id: str, payload: DowntimeCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        try:
            entity = create_downtime_segment(session, incident, payload.model_dump(), actor=actor)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_downtime", "message": str(exc)}) from exc
        return {"segment": entity_dict(entity), "metrics": calculate_metrics(session, incident), "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/recovery-actions", dependencies=[Depends(require_permission("write"))])
    def recovery_action(incident_id: str, payload: RecoveryCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        return entity_dict(create_recovery_action(session, incident, payload.model_dump(), actor=actor))

    @app.get("/api/v1/incidents/{incident_id}/metrics", dependencies=[Depends(require_permission("read"))])
    def metrics(incident_id: str, session: Session = Depends(get_session)):
        return {**calculate_metrics(session, get_or_404(session, Incident, incident_id)), "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/lifecycle-markers", dependencies=[Depends(require_permission("write"))])
    def lifecycle_marker(incident_id: str, payload: LifecycleMarkerCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        entity = session.scalar(select(IncidentLifecycleMarker).where(IncidentLifecycleMarker.incident_id == incident_id, IncidentLifecycleMarker.marker_type == payload.marker_type))
        values = payload.model_dump()
        if entity:
            for key, value in values.items(): setattr(entity, key, value)
            entity.analyst = actor
        else:
            entity = IncidentLifecycleMarker(incident_id=incident_id, analyst=actor, **values); session.add(entity)
        session.flush(); audit(session, actor=actor, action="lifecycle_marker_change", entity_type="incident_lifecycle_marker", entity_id=entity.id, details={"marker_type": entity.marker_type}); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents/{incident_id}/lifecycle-markers", dependencies=[Depends(require_permission("read"))])
    def lifecycle_markers(incident_id: str, session: Session = Depends(get_session)):
        rows = session.scalars(select(IncidentLifecycleMarker).where(IncidentLifecycleMarker.incident_id == incident_id).order_by(IncidentLifecycleMarker.occurred_at)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/recovery-milestones", dependencies=[Depends(require_permission("write"))])
    def recovery_milestone(incident_id: str, payload: RecoveryMilestoneCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        entity = RecoveryMilestone(incident_id=incident_id, analyst=actor, **payload.model_dump()); session.add(entity); session.flush()
        audit(session, actor=actor, action="recovery_milestone_create", entity_type="recovery_milestone", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.post("/api/v1/incidents/{incident_id}/event-groups", dependencies=[Depends(require_permission("write"))])
    def create_event_group(incident_id: str, payload: EventGroupCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        entity = EventGroup(incident_id=incident_id, created_by=actor, **payload.model_dump()); session.add(entity); session.flush()
        audit(session, actor=actor, action="event_group_create", entity_type="event_group", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents/{incident_id}/event-groups", dependencies=[Depends(require_permission("read"))])
    def event_groups(incident_id: str, session: Session = Depends(get_session)):
        rows = session.scalars(select(EventGroup).where(EventGroup.incident_id == incident_id).order_by(EventGroup.created_at)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/diagnostic-engagements/{engagement_id}/incident-suggestions", dependencies=[Depends(require_permission("write"))])
    def generate_suggestions(engagement_id: str, session: Session = Depends(get_session)):
        get_or_404(session, DiagnosticEngagement, engagement_id)
        return {"items": [entity_dict(row) for row in suggest_incident_windows(session, engagement_id)], "noncausal": True, "schema_version": "1.0"}

    @app.patch("/api/v1/incident-suggestions/{suggestion_id}/dismiss", dependencies=[Depends(require_permission("write"))])
    def dismiss_suggestion(suggestion_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = get_or_404(session, IncidentSuggestion, suggestion_id); entity.status = "dismissed"; entity.dismissed_by = actor; session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents/{incident_id}/dependency-impact", dependencies=[Depends(require_permission("read"))])
    def incident_dependency_impact(incident_id: str, session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        return {**dependency_impact(session, incident_id), "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/recurring-matches", dependencies=[Depends(require_permission("read"))])
    def incident_recurring_matches(incident_id: str, session: Session = Depends(get_session)):
        return {"items": recurring_matches(session, get_or_404(session, Incident, incident_id)), "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/compare/{other_id}", dependencies=[Depends(require_permission("read"))])
    def incident_compare(incident_id: str, other_id: str, session: Session = Depends(get_session)):
        return compare_incidents(session, get_or_404(session, Incident, incident_id), get_or_404(session, Incident, other_id))

    @app.post("/api/v1/incidents/{incident_id}/hypotheses", dependencies=[Depends(require_permission("write"))])
    def create_hypothesis(incident_id: str, payload: HypothesisCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        entity = RootCauseHypothesis(incident_id=incident_id, **payload.model_dump())
        session.add(entity); session.flush(); audit(session, actor=actor, action="hypothesis_change", entity_type="hypothesis", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.patch("/api/v1/hypotheses/{hypothesis_id}/status", dependencies=[Depends(require_permission("write"))])
    def hypothesis_status(hypothesis_id: str, payload: HypothesisStatusPatch, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = get_or_404(session, RootCauseHypothesis, hypothesis_id)
        if payload.status == "confirmed" and not payload.approval_status:
            raise HTTPException(status_code=422, detail={"code": "human_approval_required", "message": "confirmed hypotheses require approval_status"})
        entity.status = payload.status
        if payload.approval_status: entity.approval_status = payload.approval_status
        audit(session, actor=actor, action="hypothesis_change", entity_type="hypothesis", entity_id=entity.id, details=payload.model_dump(exclude_none=True)); session.commit()
        return entity_dict(entity)

    @app.post("/api/v1/hypotheses/{hypothesis_id}/evidence", dependencies=[Depends(require_permission("write"))])
    def add_evidence(hypothesis_id: str, payload: EvidenceCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        hypothesis = get_or_404(session, RootCauseHypothesis, hypothesis_id)
        references = [payload.canonical_event_id, payload.raw_record_id, payload.report_artifact_id]
        if payload.relation != "missing_expected" and sum(value is not None for value in references) != 1:
            raise HTTPException(status_code=422, detail={"code": "one_evidence_reference_required"})
        entity = EvidenceLink(incident_id=hypothesis.incident_id, hypothesis_id=hypothesis.id, created_by=actor, **payload.model_dump())
        session.add(entity); session.flush(); audit(session, actor=actor, action="evidence_change", entity_type="evidence_link", entity_id=entity.id); session.commit()
        recalculate_confidence(session, hypothesis)
        return {"evidence": entity_dict(entity), "hypothesis_confidence": hypothesis.confidence, "confidence_derivation": hypothesis.confidence_derivation, "schema_version": "1.0"}

    @app.post("/api/v1/evidence/{evidence_id}/review", dependencies=[Depends(require_permission("approve"))])
    def review_evidence(evidence_id: str, payload: EvidenceReviewCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = get_or_404(session, EvidenceLink, evidence_id)
        entity.review_status = payload.review_status; entity.contradiction_resolution = payload.contradiction_resolution
        audit(session, actor=actor, action="evidence_review", entity_type="evidence_link", entity_id=entity.id, details=payload.model_dump()); session.commit()
        if entity.hypothesis_id: recalculate_confidence(session, session.get(RootCauseHypothesis, entity.hypothesis_id))
        return entity_dict(entity)

    @app.post("/api/v1/hypotheses/{hypothesis_id}/reviews", dependencies=[Depends(require_permission("approve"))])
    def review_hypothesis(hypothesis_id: str, payload: HypothesisReviewCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        hypothesis = get_or_404(session, RootCauseHypothesis, hypothesis_id)
        reviewer_confidence = payload.reviewer_confidence
        disagreement = payload.decision != "accept" or (reviewer_confidence is not None and abs(reviewer_confidence - hypothesis.confidence) >= .1)
        review = HypothesisReview(
            hypothesis_id=hypothesis.id, reviewer=actor, decision=payload.decision,
            analyst_confidence=hypothesis.confidence, reviewer_confidence=reviewer_confidence,
            note=payload.note, disagreement=disagreement,
        )
        session.add(review)
        if reviewer_confidence is not None and payload.decision == "change_confidence": hypothesis.confidence = reviewer_confidence
        hypothesis.approval_status = "accepted" if payload.decision == "accept" else payload.decision
        session.flush(); audit(session, actor=actor, action="hypothesis_review", entity_type="hypothesis_review", entity_id=review.id, details={"disagreement": disagreement}); session.commit()
        return entity_dict(review)

    @app.get("/api/v1/incidents/{incident_id}/hypothesis-reviews", dependencies=[Depends(require_permission("read"))])
    def hypothesis_reviews(incident_id: str, session: Session = Depends(get_session)):
        hypothesis_ids = select(RootCauseHypothesis.id).where(RootCauseHypothesis.incident_id == incident_id)
        rows = session.scalars(select(HypothesisReview).where(HypothesisReview.hypothesis_id.in_(hypothesis_ids)).order_by(HypothesisReview.created_at)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/hypotheses", dependencies=[Depends(require_permission("read"))])
    def list_hypotheses(incident_id: str, session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        rows = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident_id).order_by(RootCauseHypothesis.confidence.desc())).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/evidence", dependencies=[Depends(require_permission("read"))])
    def list_evidence(incident_id: str, session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        rows = session.scalars(select(EvidenceLink).where(EvidenceLink.incident_id == incident_id)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/corrective-actions", dependencies=[Depends(require_permission("write"))])
    def create_corrective_action(incident_id: str, payload: CorrectiveActionCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        entity = CorrectiveAction(incident_id=incident_id, **payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="corrective_action_create", entity_type="corrective_action", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/incidents/{incident_id}/corrective-actions", dependencies=[Depends(require_permission("read"))])
    def list_corrective_actions(incident_id: str, session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        rows = session.scalars(select(CorrectiveAction).where(CorrectiveAction.incident_id == incident_id)).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/data-quality", dependencies=[Depends(require_permission("read"))])
    def data_quality(incident_id: str, session: Session = Depends(get_session)):
        return assess_incident(session, get_or_404(session, Incident, incident_id))

    @app.post("/api/v1/incidents/{incident_id}/data-quality/recalculate", dependencies=[Depends(require_permission("write"))])
    def recalculate_data_quality(incident_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        result = assess_incident(session, incident)
        audit(session, actor=actor, action="data_quality_recalculate", entity_type="incident", entity_id=incident.id, details={"score": result["score"]}); session.commit()
        return result

    @app.post("/api/v1/incidents/{incident_id}/reports", dependencies=[Depends(require_permission("write"))])
    def generate_report(incident_id: str, payload: ReportCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        try:
            return generate_report_bundle(session, incident, settings.report_root, actor=actor, included_raw_record_ids=payload.included_raw_record_ids, profile=payload.profile, redaction_rules=payload.redaction_rules)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "report_quality_blocked", "message": str(exc)}) from exc

    @app.post("/api/v1/incidents/{incident_id}/redaction-preview", dependencies=[Depends(require_permission("write"))])
    def redaction_preview(incident_id: str, payload: RedactionPreviewCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        redacted, counts = redact(payload.snapshot, payload.rules)
        entity = RedactionAudit(incident_id=incident_id, actor=actor, rules=payload.rules, replacement_counts=counts, preview_only=True)
        session.add(entity); session.flush(); audit(session, actor=actor, action="redaction_preview", entity_type="redaction_audit", entity_id=entity.id, details={"counts": counts}); session.commit()
        return {"snapshot": redacted, "replacement_counts": counts, "audit_id": entity.id, "schema_version": "1.0"}

    @app.post("/api/v1/incidents/{incident_id}/reports/{version}/approve", dependencies=[Depends(require_permission("approve"))])
    def approve_report(incident_id: str, version: int, payload: ApprovalCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        incident = get_or_404(session, Incident, incident_id)
        try:
            artifacts = approve_report_version(session, incident, version, actor=actor, note=payload.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "report_version_not_found"}) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "report_approval_blocked", "message": str(exc)}) from exc
        return {"version": version, "approved_by": actor, "artifacts": [{"id": item.id, "format": item.format, "sha256": item.sha256} for item in artifacts], "schema_version": "1.0"}

    @app.get("/api/v1/reports/{artifact_id}", dependencies=[Depends(require_permission("read"))])
    def download_report(artifact_id: str, request: Request, session: Session = Depends(get_session)):
        artifact = scoped_entity(request, session, ReportArtifact, artifact_id)
        path = Path(artifact.storage_path)
        media_types = {"json": "application/json", "markdown": "text/markdown", "html": "text/html", "pdf": "application/pdf", "timeline_csv": "text/csv", "vendor_zip": "application/zip"}
        return FileResponse(path, media_type=media_types.get(artifact.format, "application/octet-stream"), filename=path.name)

    @app.get("/api/v1/incidents/{incident_id}/reports", dependencies=[Depends(require_permission("read"))])
    def list_reports(incident_id: str, request: Request, session: Session = Depends(get_session)):
        scoped_entity(request, session, Incident, incident_id)
        rows = session.scalars(select(ReportArtifact).where(ReportArtifact.incident_id == incident_id).order_by(ReportArtifact.version.desc(), ReportArtifact.format)).all()
        return {"items": [{key: value for key, value in entity_dict(row).items() if key != "storage_path"} for row in rows], "schema_version": "1.0"}

    @app.get("/api/v1/incidents/{incident_id}/reports/compare", dependencies=[Depends(require_permission("read"))])
    def compare_report_versions(incident_id: str, left: int, right: int, session: Session = Depends(get_session)):
        get_or_404(session, Incident, incident_id)
        def snapshot(version: int):
            artifact = session.scalar(select(ReportArtifact).where(ReportArtifact.incident_id == incident_id, ReportArtifact.version == version, ReportArtifact.format == "json"))
            if not artifact: raise HTTPException(status_code=404, detail={"code": "report_version_not_found", "version": version})
            return json.loads(Path(artifact.storage_path).read_text()), artifact
        import json
        left_data, left_artifact = snapshot(left); right_data, right_artifact = snapshot(right)
        section_changes = [key for key in sorted(set(left_data) | set(right_data)) if left_data.get(key) != right_data.get(key)]
        return {
            "left": left, "right": right, "changed_sections": section_changes,
            "changed_evidence": left_data.get("evidence") != right_data.get("evidence"),
            "changed_confidence": [item.get("confidence") for item in left_data.get("hypotheses", [])] != [item.get("confidence") for item in right_data.get("hypotheses", [])],
            "changed_metrics": left_data.get("metrics") != right_data.get("metrics"),
            "approval_history": [{"version": left, "approved_by": left_artifact.approved_by}, {"version": right, "approved_by": right_artifact.approved_by}],
            "schema_version": "1.0",
        }

    @app.post("/api/v1/incidents/{incident_id}/vendor-package", dependencies=[Depends(require_permission("write"))])
    def vendor_package(incident_id: str, payload: ReportCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        result = generate_report_bundle(session, get_or_404(session, Incident, incident_id), settings.report_root, actor=actor, included_raw_record_ids=payload.included_raw_record_ids, profile="vendor_support", redaction_rules=payload.redaction_rules)
        return next(item for item in result["artifacts"] if item["format"] == "vendor_zip")

    @app.get("/api/v1/audit", dependencies=[Depends(require_permission("admin"))])
    def list_audit(request: Request, limit: int = Query(100, ge=1, le=500), session: Session = Depends(get_session)):
        query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit); scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped: query = query.where(AuditEvent.customer_id == scoped)
        rows = session.scalars(query).all()
        return {"items": [entity_dict(row) for row in rows], "schema_version": "1.0"}

    @app.post("/api/v1/diagnostic-engagements/{engagement_id}/deletion-preview", dependencies=[Depends(require_permission("admin"))])
    def deletion_preview(engagement_id: str, payload: DeletionPreviewCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        try: entity = preview_deletion(session, get_or_404(session, DiagnosticEngagement, engagement_id), actor=actor, reason=payload.reason)
        except ValueError as exc: raise HTTPException(status_code=409, detail={"code": "deletion_not_allowed", "message": str(exc)}) from exc
        return entity_dict(entity)

    @app.post("/api/v1/deletion-requests/{request_id}/approve", dependencies=[Depends(require_permission("approve"))])
    def deletion_approve(request_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        try: return entity_dict(approve_deletion(session, get_or_404(session, DeletionRequest, request_id), actor=actor))
        except ValueError as exc: raise HTTPException(status_code=409, detail={"code": "independent_approval_required", "message": str(exc)}) from exc

    @app.post("/api/v1/deletion-requests/{request_id}/execute", dependencies=[Depends(require_permission("admin"))])
    def deletion_execute(request_id: str, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        try: return entity_dict(execute_deletion(session, get_or_404(session, DeletionRequest, request_id), settings.storage_root, actor=actor))
        except ValueError as exc: raise HTTPException(status_code=409, detail={"code": "deletion_not_allowed", "message": str(exc)}) from exc

    @app.post("/api/v1/datasets", dependencies=[Depends(require_permission("write"))])
    def register_dataset(payload: DatasetRegistrationCreate, request: Request, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        if session.scalar(select(DatasetRegistration).where(DatasetRegistration.dataset_id == payload.dataset_id)):
            raise HTTPException(status_code=409, detail={"code": "dataset_id_exists"})
        if len(payload.hashes) != payload.file_count: raise HTTPException(status_code=422, detail={"code": "hash_count_mismatch"})
        customer_id = getattr(request.state, "principal", {}).get("customer_id")
        if payload.engagement_id:
            engagement = scoped_entity(request, session, DiagnosticEngagement, payload.engagement_id); customer_id = engagement.customer_id
        entity = DatasetRegistration(registered_by=actor, customer_id=customer_id, **payload.model_dump()); session.add(entity); session.flush()
        audit(session, actor=actor, action="dataset_register", entity_type="dataset_registration", entity_id=entity.id, details={"dataset_id": entity.dataset_id, "file_count": entity.file_count}); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/datasets", dependencies=[Depends(require_permission("read"))])
    def list_datasets(request: Request, session: Session = Depends(get_session)):
        query = select(DatasetRegistration).order_by(DatasetRegistration.created_at.desc()); scoped = getattr(request.state, "principal", {}).get("customer_id")
        if scoped: query = query.where(DatasetRegistration.customer_id == scoped)
        rows = session.scalars(query).all()
        return {"items": [entity_dict(row) for row in rows], "contents_exposed": False, "schema_version": "1.0"}

    @app.post("/api/v1/datasets/{registration_id}/import-effort", dependencies=[Depends(require_permission("write"))])
    def record_import_effort(registration_id: str, payload: ImportEffortCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        get_or_404(session, DatasetRegistration, registration_id)
        entity = ImportEffortRecord(dataset_registration_id=registration_id, **payload.model_dump()); session.add(entity); session.flush()
        audit(session, actor=actor, action="import_effort_record", entity_type="dataset_registration", entity_id=registration_id, details={"record_id": entity.id, "reusable_percentage": entity.reusable_percentage}); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/datasets/{registration_id}/import-effort", dependencies=[Depends(require_permission("read"))])
    def import_effort(registration_id: str, session: Session = Depends(get_session)):
        get_or_404(session, DatasetRegistration, registration_id)
        rows = session.scalars(select(ImportEffortRecord).where(ImportEffortRecord.dataset_registration_id == registration_id)).all()
        total = sum(row.analyst_minutes + row.developer_minutes for row in rows)
        reusable = sum(row.reusable_percentage for row in rows) / len(rows) if rows else None
        return {"items": [entity_dict(row) for row in rows], "total_person_minutes": total, "average_reusable_percentage": reusable, "schema_version": "1.0"}

    @app.post("/api/v1/validation-records", dependencies=[Depends(require_permission("write"))])
    def create_validation_record(payload: ValidationRecordCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        entity = ValidationRecord(**payload.model_dump()); session.add(entity); session.flush(); audit(session, actor=actor, action="validation_record_create", entity_type="validation_record", entity_id=entity.id); session.commit()
        return entity_dict(entity)

    @app.get("/api/v1/validation-records", dependencies=[Depends(require_permission("read"))])
    def list_validation_records(session: Session = Depends(get_session)):
        rows = session.scalars(select(ValidationRecord).order_by(ValidationRecord.occurred_at.desc())).all()
        return {"items": [entity_dict(row) for row in rows], "gate_policy": "Synthetic records never satisfy commercial gates.", "schema_version": "1.0"}

    @app.post("/api/v1/validation-decisions", dependencies=[Depends(require_permission("write"))])
    def create_validation_decision(payload: ValidationDecisionCreate, actor: str = Depends(actor_header), session: Session = Depends(get_session)):
        records = session.scalars(select(ValidationRecord).where(ValidationRecord.id.in_(payload.validation_record_ids))).all()
        if len(records) != len(set(payload.validation_record_ids)):
            raise HTTPException(status_code=422, detail={"code": "missing_validation_evidence"})
        entity = ValidationDecision(decision=payload.decision, rationale=payload.rationale, validation_record_ids=payload.validation_record_ids, created_by=actor)
        session.add(entity); session.flush(); audit(session, actor=actor, action="validation_decision", entity_type="validation_decision", entity_id=entity.id, details={"decision": entity.decision, "evidence_ids": entity.validation_record_ids}); session.commit()
        return entity_dict(entity)

    return app


app = create_app()
