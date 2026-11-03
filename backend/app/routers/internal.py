import hmac

from fastapi import APIRouter, Depends, Header

from ..config import get_settings
from ..errors import ApiError
from ..jobs import background

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


def require_token(authorization: str = Header("")) -> None:
    token = get_settings().ingest_token
    if not token:
        raise ApiError(404, "not_found", "Not Found")
    given = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(given, token):
        raise ApiError(401, "unauthorized", "Token non valido.")


@router.post("/ingest", status_code=202, dependencies=[Depends(require_token)])
def ingest(chart_only: bool = False):
    started = background.start(chart_only)
    return {"started": started, "status": background.status}


@router.get("/ingest", dependencies=[Depends(require_token)])
def ingest_status():
    return background.status
