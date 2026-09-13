from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AuthIdentity:
    subject: str
    email: str
    role: str
    customer_id: str | None
    provider: str


class AuthenticationProvider(Protocol):
    def authenticate(self, credential: str) -> AuthIdentity: ...
    def logout_url(self, return_to: str) -> str | None: ...


@dataclass(frozen=True)
class OIDCConfiguration:
    issuer: str
    client_id: str
    audience: str
    role_claim: str = "groups"
    role_mapping: dict[str, str] | None = None
    local_fallback_enabled: bool = False

    def validate(self) -> None:
        if not self.issuer.startswith("https://"): raise ValueError("OIDC issuer must use HTTPS")
        if not self.client_id or not self.audience: raise ValueError("OIDC client ID and audience are required")
        if self.local_fallback_enabled: raise ValueError("local fallback must remain disabled when OIDC is active")
