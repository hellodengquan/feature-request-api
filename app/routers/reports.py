from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.cache import get_cached_topic_count
from app.database import get_db
from app.i18n import t
from app.models import Feedback, Topic, FeedbackStatus, PriorityLevel
from app.schemas import FeedbackListItem, PendingEvaluationReport, FeedbackGroupByTopic, TopicOut

router = APIRouter(prefix="/reports", tags=["reports"])


def _current_utc_offset() -> str:
    now = datetime.now(timezone.utc)
    local_now = datetime.now()
    offset = local_now.utcoffset()
    if offset is None:
        return "+00:00"
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


@router.get("/pending-evaluation", response_model=PendingEvaluationReport)
def pending_evaluation_report(
    request: Request,
    source: Optional[str] = None,
    priority: Optional[PriorityLevel] = None,
    created_from: Optional[datetime] = Query(
        None,
        description="创建时间起始（含），ISO 格式，如 2026-06-01T00:00:00。服务器时区为 UTC，offset 标注见响应 timezone_offset 字段",
    ),
    created_to: Optional[datetime] = Query(
        None,
        description="创建时间截止（含），ISO 格式，如 2026-06-30T23:59:59。服务器时区为 UTC，offset 标注见响应 timezone_offset 字段",
    ),
    skip: int = Query(0, ge=0, description="分页偏移"),
    limit: int = Query(200, ge=1, le=2000, description="每页数量"),
    db: Session = Depends(get_db),
):
    query = db.query(Feedback).filter(Feedback.status == FeedbackStatus.PENDING)
    if source:
        query = query.filter(Feedback.source == source)
    if priority:
        query = query.filter(Feedback.priority == priority)
    if created_from:
        query = query.filter(Feedback.created_at >= created_from)
    if created_to:
        query = query.filter(Feedback.created_at <= created_to)
    total = query.count()
    feedbacks = query.order_by(Feedback.created_at.asc()).offset(skip).limit(limit).all()
    return PendingEvaluationReport(
        total=total,
        feedbacks=[FeedbackListItem.model_validate(f) for f in feedbacks],
        timezone_offset=_current_utc_offset(),
    )


@router.get("/pending-evaluation/by-topic", response_model=list)
def pending_evaluation_grouped_by_topic(
    request: Request,
    created_from: Optional[datetime] = Query(
        None,
        description="创建时间起始（含），服务器时区为 UTC，offset 见响应",
    ),
    created_to: Optional[datetime] = Query(
        None,
        description="创建时间截止（含），服务器时区为 UTC，offset 见响应",
    ),
    topic_skip: int = Query(0, ge=0, description="主题列表分页偏移"),
    topic_limit: int = Query(50, ge=1, le=500, description="主题列表每页数量"),
    feedback_skip: int = Query(0, ge=0, description="每个主题下反馈的分页偏移"),
    feedback_limit: int = Query(100, ge=1, le=1000, description="每个主题下反馈每页数量"),
    db: Session = Depends(get_db),
):
    base_filter = [Feedback.status == FeedbackStatus.PENDING]
    if created_from:
        base_filter.append(Feedback.created_at >= created_from)
    if created_to:
        base_filter.append(Feedback.created_at <= created_to)

    topics = db.query(Topic).order_by(Topic.id.asc()).offset(topic_skip).limit(topic_limit).all()
    result = []
    for topic in topics:
        feedbacks = (
            db.query(Feedback)
            .filter(*base_filter, Feedback.topic_id == topic.id)
            .order_by(Feedback.created_at.asc())
            .offset(feedback_skip)
            .limit(feedback_limit)
            .all()
        )
        total_count = get_cached_topic_count(topic.id)
        if feedbacks or total_count > 0:
            result.append(
                FeedbackGroupByTopic(
                    topic=TopicOut.model_validate(topic),
                    feedbacks=[FeedbackListItem.model_validate(f) for f in feedbacks],
                    feedback_count=total_count,
                )
            )
    ungrouped = (
        db.query(Feedback)
        .filter(*base_filter, Feedback.topic_id.is_(None))
        .order_by(Feedback.created_at.asc())
        .offset(feedback_skip)
        .limit(feedback_limit)
        .all()
    )
    ungrouped_total = get_cached_topic_count(None)
    if ungrouped or ungrouped_total > 0:
        result.append(
            FeedbackGroupByTopic(
                topic=None,
                feedbacks=[FeedbackListItem.model_validate(f) for f in ungrouped],
                feedback_count=ungrouped_total,
            )
        )
    return result
