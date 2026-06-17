import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import List, Optional, Set

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from jose import JWTError, jwt

from app.i18n import t

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "feature-request-pool-secret-key")
JWT_ALGORITHM = "HS256"
JWT_ROTATION_VERSION = int(os.environ.get("JWT_ROTATION_VERSION", "1"))

BLACKLIST_KEY_PREFIX = "jwt_blacklist:"
REVOKED_USERS_KEY = "jwt_revoked_users"
ROTATION_VERSION_KEY = "jwt_rotation_version"
BLACKLIST_TTL_SECONDS = 86400 * 7


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
    jti: str = ""


_memory_blacklist: Set[str] = set()
_memory_revoked_users: Set[str] = set()
_memory_rotation_version: int = JWT_ROTATION_VERSION


def _get_redis():
    try:
        from app.cache import get_redis
        r = get_redis()
        r.ping()
        return r
    except Exception:
        return None


def _is_token_blacklisted(jti: str) -> bool:
    if jti in _memory_blacklist:
        return True
    r = _get_redis()
    if r:
        try:
            return bool(r.exists(f"{BLACKLIST_KEY_PREFIX}{jti}"))
        except Exception:
            pass
    return False


def _is_user_revoked(user_id: str) -> bool:
    if user_id in _memory_revoked_users:
        return True
    r = _get_redis()
    if r:
        try:
            return bool(r.sismember(REVOKED_USERS_KEY, user_id))
        except Exception:
            pass
    return False


def _get_current_rotation_version() -> int:
    r = _get_redis()
    if r:
        try:
            v = r.get(ROTATION_VERSION_KEY)
            if v is not None:
                return int(v)
        except Exception:
            pass
    return _memory_rotation_version


def blacklist_token(jti: str, ttl: int = BLACKLIST_TTL_SECONDS):
    _memory_blacklist.add(jti)
    r = _get_redis()
    if r:
        try:
            r.setex(f"{BLACKLIST_KEY_PREFIX}{jti}", ttl, "1")
        except Exception:
            logger.warning("Failed to blacklist token jti=%s in Redis", jti)


def revoke_user(user_id: str):
    _memory_revoked_users.add(user_id)
    r = _get_redis()
    if r:
        try:
            r.sadd(REVOKED_USERS_KEY, user_id)
        except Exception:
            logger.warning("Failed to revoke user %s in Redis", user_id)


def unrevoke_user(user_id: str):
    _memory_revoked_users.discard(user_id)
    r = _get_redis()
    if r:
        try:
            r.srem(REVOKED_USERS_KEY, user_id)
        except Exception:
            logger.warning("Failed to unrevoke user %s in Redis", user_id)


def rotate_jwt_secret(new_version: int):
    global _memory_rotation_version
    _memory_rotation_version = new_version
    r = _get_redis()
    if r:
        try:
            r.set(ROTATION_VERSION_KEY, str(new_version))
        except Exception:
            logger.warning("Failed to set rotation version in Redis")


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
    return UserIdentity(user_id=f"hdr-{x_user}", username=x_user, role=role, original_token="", jti="")


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

        jti = payload.get("jti", "")
        token_rot = payload.get("rot", 0)
        current_rot = _get_current_rotation_version()
        if token_rot < current_rot:
            raise HTTPException(status_code=401, detail=t("jwt_rotated", accept_lang))

        if jti and _is_token_blacklisted(jti):
            raise HTTPException(status_code=401, detail=t("jwt_revoked", accept_lang))

        user_id = str(payload.get("user_id") or payload.get("sub") or "unknown")
        if _is_user_revoked(user_id):
            raise HTTPException(status_code=401, detail=t("account_revoked", accept_lang))

        try:
            role = UserRole(payload.get("role", "viewer"))
        except (ValueError, Exception):
            role = UserRole.VIEWER
        username = payload.get("username") or payload.get("sub") or "unknown"
        return UserIdentity(user_id=user_id, username=username, role=role, original_token=token, jti=jti)

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


async def require_admin_user(
    user: UserIdentity = Depends(require_user),
    request: Request = Request,
) -> UserIdentity:
    accept_lang = request.headers.get("accept-language") if hasattr(request, "headers") else None
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=t("role_admin_denied", accept_lang))
    return user


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/revoke")
def revoke_token_endpoint(
    request: Request,
    jti: Optional[str] = None,
    user_id: Optional[str] = None,
    _admin: UserIdentity = Depends(require_admin_user),
):
    accept_lang = request.headers.get("accept-language")
    if not jti and not user_id:
        raise HTTPException(status_code=400, detail=t("revoke_params_required", accept_lang))
    if jti:
        blacklist_token(jti)
    if user_id:
        revoke_user(user_id)
    return {"revoked": True, "jti": jti, "user_id": user_id}


@auth_router.post("/unrevoke")
def unrevoke_user_endpoint(
    request: Request,
    user_id: str,
    _admin: UserIdentity = Depends(require_admin_user),
):
    unrevoke_user(user_id)
    return {"unrevoked": True, "user_id": user_id}


@auth_router.post("/rotate")
def rotate_secret_endpoint(
    request: Request,
    new_version: int,
    _admin: UserIdentity = Depends(require_admin_user),
):
    accept_lang = request.headers.get("accept-language")
    current = _get_current_rotation_version()
    if new_version <= current:
        raise HTTPException(status_code=400, detail=t("rotate_version_invalid", accept_lang))
    rotate_jwt_secret(new_version)
    return {"rotated": True, "old_version": current, "new_version": new_version}
