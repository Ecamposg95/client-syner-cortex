"""Centralized runtime configuration sourced from environment variables.

Security-sensitive values (JWT secret, CORS origins) are read from the
environment. In production (ENV=production) missing critical values raise at
import time so the app fails fast; in development a stable, clearly-insecure
fallback keeps local workflows running.
"""
import os
from dotenv import load_dotenv

# Load a local .env (if present) so DATABASE_URL / JWT_SECRET / CORS_ORIGINS are
# picked up automatically on every start.
load_dotenv()

ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV.lower() in ("production", "prod")

# ── JWT ────────────────────────────────────────────────────────────────────
# Dev fallback keeps existing local sessions valid; production MUST set JWT_SECRET.
_DEV_JWT_FALLBACK = "super_secret_key_cortex_2026_syner"


def _resolve_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    if IS_PRODUCTION:
        raise RuntimeError(
            "JWT_SECRET environment variable must be set in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    return _DEV_JWT_FALLBACK


JWT_SECRET = _resolve_jwt_secret()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# ── CORS ───────────────────────────────────────────────────────────────────
# Comma-separated list in CORS_ORIGINS; dev default targets the Vite dev server.
_DEV_CORS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def _resolve_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return _DEV_CORS


CORS_ORIGINS = _resolve_cors_origins()

# ── Password policy ────────────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))

# ── Rate limiting (anti brute-force on /auth) ──────────────────────────────
# Per-client-IP limits applied to the authentication endpoints. Tune via env;
# set RATE_LIMIT_ENABLED=false to disable entirely (e.g. for load tests).
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in (
    "1", "true", "yes", "on",
)
AUTH_LOGIN_RATE_LIMIT = os.getenv("AUTH_LOGIN_RATE_LIMIT", "10/minute")
AUTH_SIGNUP_RATE_LIMIT = os.getenv("AUTH_SIGNUP_RATE_LIMIT", "5/minute")
