import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .errors import ApiError
from .models import Role, User, UserSession

SESSION_COOKIE = "sonora_session"
_ph = PasswordHasher()


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(UserSession(user_id=user.id, token_hash=_token_hash(token),
                       expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().session_days)))
    return token


def revoke_session(db: Session, token: str | None) -> None:
    if not token:
        return
    s = db.scalar(select(UserSession).where(UserSession.token_hash == _token_hash(token)))
    if s and not s.revoked_at:
        s.revoked_at = datetime.now(timezone.utc)


def cookie_kwargs() -> dict:
    s = get_settings()
    return {"httponly": True, "secure": s.is_production, "samesite": "lax",
            "max_age": s.session_days * 86400, "path": "/"}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    s = db.scalar(select(UserSession).where(UserSession.token_hash == _token_hash(token)))
    if not s or s.revoked_at or _aware(s.expires_at) < datetime.now(timezone.utc):
        return None
    user = db.get(User, s.user_id)
    if not user or user.deleted_at:
        return None
    return user


def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if not user:
        raise ApiError(401, "unauthorized", "Accedi per continuare.")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != Role.admin:
        raise ApiError(403, "forbidden", "Serve un account amministratore.")
    return user
