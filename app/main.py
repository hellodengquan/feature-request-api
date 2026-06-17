from fastapi import FastAPI

from app.database import engine, Base
from app.routers import customers, topics, feedbacks, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="产品功能需求池 API",
    description="集中管理研发、销售、客服收集的用户反馈，支持分类、查询和待评估清单生成",
    version="1.0.0",
)

app.include_router(customers.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(feedbacks.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "产品功能需求池 API 服务运行中", "docs": "/docs"}
