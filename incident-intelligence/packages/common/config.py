from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str
    storage_root: Path
    max_upload_bytes: int
    allowed_origins: tuple[str, ...]
    app_env: str
    auth_required: bool = False
    secret_key: str = "development-only-change-me"
    token_expire_minutes: int = 60
    evidence_encryption_key: bytes | None = None
    evidence_encryption_key_id: str = ""
    login_attempt_limit: int = 5

    @property
    def upload_root(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def report_root(self) -> Path:
        return self.storage_root / "reports"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "RFII_DATABASE_URL", f"sqlite:///{ROOT / 'storage' / 'incident_intelligence.db'}"
        ),
        storage_root=Path(os.getenv("RFII_STORAGE_ROOT", str(ROOT / "storage"))).resolve(),
        max_upload_bytes=int(os.getenv("RFII_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        allowed_origins=tuple(
            value.strip()
            for value in os.getenv("RFII_CORS_ORIGINS", "http://localhost:8000").split(",")
            if value.strip()
        ),
        app_env=os.getenv("RFII_APP_ENV", "development"),
        auth_required=os.getenv("RFII_AUTH_REQUIRED", "false").lower() == "true",
        secret_key=os.getenv("RFII_SECRET_KEY", "development-only-change-me"),
        token_expire_minutes=int(os.getenv("RFII_TOKEN_EXPIRE_MINUTES", "60")),
        evidence_encryption_key=base64.b64decode(os.environ["RFII_EVIDENCE_KEY_B64"]) if os.getenv("RFII_EVIDENCE_KEY_B64") else None,
        evidence_encryption_key_id=os.getenv("RFII_EVIDENCE_KEY_ID", ""),
        login_attempt_limit=int(os.getenv("RFII_LOGIN_ATTEMPT_LIMIT", "5")),
    )
