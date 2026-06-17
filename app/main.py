from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.cache import close_redis, refresh_topic_counts_async
from app.database import engine, Base
from app.i18n import t
from app.routers import customers, topics, feedbacks, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="产品功能需求池 API",
    description="集中管理研发、销售、客服收集的用户反馈，支持分类、查询和待评估清单生成",
    version="1.1.0",
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


@app.on_event("startup")
async def on_startup():
    refresh_topic_counts_async()


@app.on_event("shutdown")
async def on_shutdown():
    close_redis()


app.include_router(customers.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(feedbacks.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "产品功能需求池 API 服务运行中", "docs": "/docs"}
