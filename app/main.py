from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth import UserIdentity, decode_jwt_token, auth_router
from app.cache import close_redis, refresh_hot_topic_counts_async
from app.database import engine, Base
from app.i18n import t
from app.routers import customers, topics, feedbacks, reports

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        refresh_hot_topic_counts_async()
    except Exception:
        logger.warning("Hot-topic warm-up failed during startup, service continues normally")
    yield
    close_redis()


app = FastAPI(
    title="产品功能需求池 API",
    description="集中管理研发、销售、客服收集的用户反馈，支持分类、查询和待评估清单生成",
    version="1.3.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    accept_lang = request.headers.get("accept-language")
    errors = []
    for err in exc.errors():
        field_path = ".".join(str(loc) for loc in err.get("loc", []))
        if err.get("type") == "enum":
            if "priority" in field_path:
                msg = t("enum_priority", accept_lang)
            elif "status" in field_path:
                msg = t("enum_status", accept_lang)
            else:
                msg = err.get("msg", "")
        elif "changed_by" in field_path:
            msg = t("changed_by_required", accept_lang)
        else:
            msg = err.get("msg", "")
        errors.append({"loc": list(err.get("loc", [])), "msg": msg, "type": err.get("type", "")})
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(auth_router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(feedbacks.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "产品功能需求池 API 服务运行中",
        "docs": "/docs",
        "alembic_migrations": {
            "postgresql": "migrations/postgresql/",
            "mysql": "migrations/mysql/",
        },
        "authentication": {
            "scheme": "Bearer JWT",
            "supported_roles": ["admin", "pm", "dev", "sales", "support", "viewer"],
            "features": ["token_blacklist", "rotation", "account_revocation"],
        },
        "i18n": {
            "supported_languages": ["zh", "en", "ja", "ko", "ru"],
            "header": "Accept-Language",
            "locale_formatting": True,
        },
    }


@app.get("/auth/jwt-example")
def get_jwt_example():
    import uuid
    import datetime

    from jose import jwt

    from app.auth import JWT_ALGORITHM, JWT_SECRET, _get_current_rotation_version

    current_rot = _get_current_rotation_version()
    now = datetime.datetime.utcnow()
    examples = {}
    for role_name in ["admin", "pm", "dev", "sales", "support", "viewer"]:
        jti = str(uuid.uuid4())
        payload = {
            "user_id": role_name,
            "username": f"test-{role_name}",
            "role": role_name,
            "jti": jti,
            "rot": current_rot,
            "iat": now,
            "exp": now + datetime.timedelta(days=365),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        examples[role_name] = {
            "header": f"Authorization: Bearer {token}",
            "fallback_headers": f"X-User: test-{role_name} | X-Role: {role_name}",
            "jti": jti,
            "rot": current_rot,
        }
    return examples
