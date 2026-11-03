from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..errors import ApiError
from ..models import AuditLog, User, UserSession
from ..schemas import DeleteAccountIn, LoginIn, RegisterIn, UserOut
from ..security import (SESSION_COOKIE, cookie_kwargs, create_session, current_user, current_user_optional,
                        hash_password, revoke_session, verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])
# hash fittizio per tempi di risposta uguali con email inesistente
_DUMMY_HASH = hash_password("sonora-timing-equalizer")


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if not body.confirm_min_age:
        raise ApiError(422, "age_required", f"Per usare SONORA devi avere almeno {get_settings().min_age} anni.")
    email = body.email.lower()
    if db.scalar(select(User).where(or_(User.email == email, User.username == body.username))):
        raise ApiError(409, "already_exists", "Email o nome utente già in uso.")
    user = User(email=email, username=body.username, display_name=body.display_name,
                password_hash=hash_password(body.password), age_confirmed_at=datetime.now(timezone.utc))
    db.add(user)
    db.flush()
    token = create_session(db, user)
    db.add(AuditLog(actor_user_id=user.id, action="user.register", target_type="user", target_id=str(user.id)))
    db.commit()
    response.set_cookie(SESSION_COOKIE, token, **cookie_kwargs())
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower(), User.deleted_at.is_(None)))
    ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok:
        raise ApiError(401, "invalid_credentials", "Email o password non corrette.")
    token = create_session(db, user)
    db.commit()
    response.set_cookie(SESSION_COOKIE, token, **cookie_kwargs())
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    revoke_session(db, request.cookies.get(SESSION_COOKIE))
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.status_code = 204
    return response


@router.get("/session")
def session(user: User | None = Depends(current_user_optional)):
    """Come /me ma risponde sempre 200: {"user": null} se non c'è una sessione valida."""
    return {"user": UserOut.model_validate(user).model_dump(mode="json") if user else None}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.delete("/account", status_code=204)
def delete_account(body: DeleteAccountIn, response: Response, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Cancellazione GDPR: anonimizza subito i dati personali e revoca tutte le sessioni.
    Like, raccolte e attività vengono rimossi in cascata quando la riga utente viene eliminata
    dal job di pulizia (vedi docs/PRIVACY_RETENTION.md)."""
    if not verify_password(body.password, user.password_hash):
        raise ApiError(401, "invalid_credentials", "Password non corretta.")
    now = datetime.now(timezone.utc)
    uid = user.id
    user.email = f"deleted-{uid.hex}@invalid"
    user.username = f"deleted_{uid.hex[:20]}"
    user.display_name = "Account eliminato"
    user.avatar_url = None
    user.password_hash = None
    user.deleted_at = now
    db.execute(update(UserSession).where(UserSession.user_id == uid, UserSession.revoked_at.is_(None))
               .values(revoked_at=now))
    db.add(AuditLog(actor_user_id=uid, action="user.delete", target_type="user", target_id=str(uid)))
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.status_code = 204
    return response
