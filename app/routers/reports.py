from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackListItem, PendingEvaluationReport, FeedbackGroupByTopic, TopicOut
from app.models import Topic

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/pending-evaluation", response_model=PendingEvaluationReport)
def pending_evaluation_report(
    source: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Feedback).filter(Feedback.status == "pending")
    if source:
        query = query.filter(Feedback.source == source)
    if priority:
        query = query.filter(Feedback.priority == priority)
    feedbacks = query.order_by(Feedback.created_at.asc()).all()
    return PendingEvaluationReport(
        total=len(feedbacks),
        feedbacks=[FeedbackListItem.model_validate(f) for f in feedbacks],
    )


@router.get("/pending-evaluation/by-topic", response_model=list)
def pending_evaluation_grouped_by_topic(db: Session = Depends(get_db)):
    topics = db.query(Topic).all()
    result = []
    for topic in topics:
        feedbacks = (
            db.query(Feedback)
            .filter(Feedback.status == "pending", Feedback.topic_id == topic.id)
            .order_by(Feedback.created_at.asc())
            .all()
        )
        if feedbacks:
            result.append(
                FeedbackGroupByTopic(
                    topic=TopicOut.model_validate(topic),
                    feedbacks=[FeedbackListItem.model_validate(f) for f in feedbacks],
                )
            )
    ungrouped = (
        db.query(Feedback)
        .filter(Feedback.status == "pending", Feedback.topic_id.is_(None))
        .order_by(Feedback.created_at.asc())
        .all()
    )
    if ungrouped:
        result.append(
            FeedbackGroupByTopic(
                topic=None,
                feedbacks=[FeedbackListItem.model_validate(f) for f in ungrouped],
            )
        )
    return result
