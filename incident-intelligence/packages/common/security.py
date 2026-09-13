from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
import secrets


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(derived).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, work_factor, salt_b64, hash_b64 = encoded.split("$", 3)
        if algorithm != "scrypt": return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(hash_b64)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=int(work_factor), r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(*, user_id: str, role: str, token_version: int, secret_key: str, expire_minutes: int) -> str:
    payload = {"sub": user_id, "role": role, "ver": token_version, "exp": int((datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)).timestamp())}
    body = _b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _b64(hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_token(token: str, *, secret_key: str) -> dict:
    body, signature = token.split(".", 1)
    expected = _b64(hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected): raise ValueError("invalid token signature")
    payload = json.loads(_unb64(body))
    if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()): raise ValueError("token expired")
    return payload


def new_reset_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()
