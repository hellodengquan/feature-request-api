from dataclasses import dataclass
from enum import Enum as PyEnum
from typing import List, Optional

from fastapi import Depends, Header, HTTPException, Request
from jose import JWTError, jwt

from app.i18n import t

JWT_SECRET = "feature-request-pool-secret-key"
JWT_ALGORITHM = "HS256"


class UserRole(str, PyEnum):
    ADMIN = "admin"
    PM = "pm"
    DEV = "dev"
    SALES = "sales"
    SUPPORT = "support"
    VIEWER = "viewer"


ALLOWED_WRITE_ROLES = {UserRole.ADMIN, UserRole.PM, UserRole.DEV, UserRole.SALES, UserRole.SUPPORT}
ALLOWED_STATUS_CHANGE_ROLES = {UserRole.ADMIN, UserRole.PM}
ALLOWED_DELETE_ROLES = {UserRole.ADMIN, UserRole.PM}


@dataclass
class UserIdentity:
    user_id: str
    username: str
    role: UserRole
    original_token: str


def _parse_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    if len(parts) == 1:
        return parts[0]
    return None


def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (JWTError, Exception):
        return None


def _fallback_user_from_header(x_user: Optional[str], x_role: Optional[str]) -> Optional[UserIdentity]:
    if not x_user:
        return None
    try:
        role = UserRole(x_role) if x_role else UserRole.VIEWER
    except (ValueError, Exception):
        role = UserRole.VIEWER
    return UserIdentity(user_id=f"hdr-{x_user}", username=x_user, role=role, original_token="")


async def require_user(
    request: Request,
    authorization: Optional[str] = Header(None, description="Bearer JWT token"),
    x_user: Optional[str] = Header(None, description="Fallback user header for dev/testing"),
    x_role: Optional[str] = Header(None, description="Fallback role header for dev/testing"),
) -> UserIdentity:
    accept_lang = request.headers.get("accept-language")
    token = _parse_bearer_token(authorization)

    if token:
        payload = decode_jwt_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail=t("jwt_invalid", accept_lang))
        try:
            role = UserRole(payload.get("role", "viewer"))
        except (ValueError, Exception):
            role = UserRole.VIEWER
        username = payload.get("username") or payload.get("sub") or "unknown"
        user_id = str(payload.get("user_id") or payload.get("sub") or username)
        return UserIdentity(user_id=user_id, username=username, role=role, original_token=token)

    fallback = _fallback_user_from_header(x_user, x_role)
    if fallback:
        return fallback

    raise HTTPException(status_code=401, detail=t("jwt_missing", accept_lang))


async def require_write_user(
    user: UserIdentity = Depends(require_user),
    request: Request = Request,
) -> UserIdentity:
    accept_lang = request.headers.get("accept-language") if hasattr(request, "headers") else None
    if user.role not in ALLOWED_WRITE_ROLES:
        raise HTTPException(status_code=403, detail=t("role_write_denied", accept_lang))
    return user


async def require_status_change_user(
    user: UserIdentity = Depends(require_user),
    request: Request = Request,
) -> UserIdentity:
    accept_lang = request.headers.get("accept-language") if hasattr(request, "headers") else None
    if user.role not in ALLOWED_STATUS_CHANGE_ROLES:
        raise HTTPException(status_code=403, detail=t("role_status_change_denied", accept_lang))
    return user


async def require_delete_user(
    user: UserIdentity = Depends(require_user),
    request: Request = Request,
) -> UserIdentity:
    accept_lang = request.headers.get("accept-language") if hasattr(request, "headers") else None
    if user.role not in ALLOWED_DELETE_ROLES:
        raise HTTPException(status_code=403, detail=t("role_delete_denied", accept_lang))
    return user
