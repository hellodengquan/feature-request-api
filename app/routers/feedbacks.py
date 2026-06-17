from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.auth import (
    UserIdentity,
    require_user,
    require_write_user,
    require_status_change_user,
    require_delete_user,
)
from app.cache import get_cached_topic_count, invalidate_topic_count, invalidate_all_topic_counts
from app.database import get_db
from app.i18n import t
from app.models import Feedback, Customer, Topic, StatusChange, feedback_customer, PriorityLevel, FeedbackStatus
from app.schemas import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackOut,
    FeedbackListItem,
    FeedbackGroupByTopic,
    StatusChangeCreate,
    StatusChangeOut,
    TopicOut,
)

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


def _resolve_changed_by(data_changed_by: Optional[str], user: UserIdentity) -> str:
    if data_changed_by and data_changed_by.strip():
        return data_changed_by.strip()
    return user.username or user.user_id


@router.post("/", response_model=FeedbackOut, status_code=201)
def create_feedback(
    data: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_write_user),
):
    accept_lang = request.headers.get("accept-language")
    customer_ids = data.customer_ids or []
    if data.topic_id:
        topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
        if not topic:
            raise HTTPException(status_code=400, detail=t("topic_not_found", accept_lang))
    customers = db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
    if len(customers) != len(customer_ids):
        raise HTTPException(status_code=400, detail=t("customer_not_found", accept_lang))

    feedback = Feedback(
        description=data.description,
        impact_scope=data.impact_scope,
        priority=data.priority,
        status=data.status,
        source=data.source,
        topic_id=data.topic_id,
        customers=customers,
    )
    db.add(feedback)
    db.flush()
    if data.status and data.status != FeedbackStatus.PENDING:
        initial_change = StatusChange(
            feedback_id=feedback.id,
            old_status=FeedbackStatus.PENDING,
            new_status=data.status,
            changed_by=user.username or user.user_id,
            remark="创建时指定初始状态",
        )
        db.add(initial_change)
    db.commit()
    db.refresh(feedback)
    invalidate_all_topic_counts()
    return db.query(Feedback).options(
        joinedload(Feedback.customers), joinedload(Feedback.status_changes)
    ).filter(Feedback.id == feedback.id).first()


@router.get("/", response_model=List[FeedbackListItem])
def list_feedbacks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[FeedbackStatus] = None,
    priority: Optional[PriorityLevel] = None,
    source: Optional[str] = None,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_user),
):
    query = db.query(Feedback)
    if status:
        query = query.filter(Feedback.status == status)
    if priority:
        query = query.filter(Feedback.priority == priority)
    if source:
        query = query.filter(Feedback.source == source)
    if topic_id is not None:
        query = query.filter(Feedback.topic_id == topic_id)
    return query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/by-topic", response_model=List[FeedbackGroupByTopic])
def list_feedbacks_grouped_by_topic(
    topic_skip: int = Query(0, ge=0, description="主题列表分页偏移"),
    topic_limit: int = Query(50, ge=1, le=500, description="主题列表每页数量"),
    feedback_skip: int = Query(0, ge=0, description="每个主题下反馈的分页偏移"),
    feedback_limit: int = Query(100, ge=1, le=1000, description="每个主题下反馈每页数量"),
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_user),
):
    topics = db.query(Topic).order_by(Topic.id.asc()).offset(topic_skip).limit(topic_limit).all()
    result = []
    for topic in topics:
        feedbacks = (
            db.query(Feedback)
            .filter(Feedback.topic_id == topic.id)
            .order_by(Feedback.created_at.desc())
            .offset(feedback_skip)
            .limit(feedback_limit)
            .all()
        )
        total_count = get_cached_topic_count(topic.id)
        result.append(
            FeedbackGroupByTopic(
                topic=TopicOut.model_validate(topic),
                feedbacks=[FeedbackListItem.model_validate(f) for f in feedbacks],
                feedback_count=total_count,
            )
        )
    ungrouped = (
        db.query(Feedback)
        .filter(Feedback.topic_id.is_(None))
        .order_by(Feedback.created_at.desc())
        .offset(feedback_skip)
        .limit(feedback_limit)
        .all()
    )
    if ungrouped or topic_skip == 0:
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


@router.get("/by-customer/{customer_id}", response_model=List[FeedbackListItem])
def list_feedbacks_by_customer(
    customer_id: int,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_user),
):
    accept_lang = request.headers.get("accept-language")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=t("customer_not_found_single", accept_lang))
    feedbacks = (
        db.query(Feedback)
        .join(feedback_customer)
        .filter(feedback_customer.c.customer_id == customer_id)
        .order_by(Feedback.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return feedbacks


@router.get("/{feedback_id}", response_model=FeedbackOut)
def get_feedback(
    feedback_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_user),
):
    accept_lang = request.headers.get("accept-language")
    feedback = (
        db.query(Feedback)
        .options(joinedload(Feedback.customers), joinedload(Feedback.status_changes))
        .filter(Feedback.id == feedback_id)
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail=t("feedback_not_found", accept_lang))
    return feedback


@router.put("/{feedback_id}", response_model=FeedbackOut)
def update_feedback(
    feedback_id: int,
    data: FeedbackUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_write_user),
):
    accept_lang = request.headers.get("accept-language")
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail=t("feedback_not_found", accept_lang))
    if data.topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
        if not topic:
            raise HTTPException(status_code=400, detail=t("topic_not_found", accept_lang))

    old_status = feedback.status
    update_data = data.model_dump(exclude_unset=True, exclude={"customer_ids", "changed_by", "remark"})
    for key, value in update_data.items():
        setattr(feedback, key, value)

    if "status" in update_data and old_status != update_data["status"]:
        from app.auth import ALLOWED_STATUS_CHANGE_ROLES

        if user.role not in ALLOWED_STATUS_CHANGE_ROLES:
            raise HTTPException(status_code=403, detail=t("role_status_change_denied", accept_lang))
        changed_by = _resolve_changed_by(data.changed_by, user)
        status_change = StatusChange(
            feedback_id=feedback_id,
            old_status=old_status,
            new_status=update_data["status"],
            changed_by=changed_by,
            remark=data.remark or "",
        )
        db.add(status_change)

    if data.customer_ids is not None:
        customers = db.query(Customer).filter(Customer.id.in_(data.customer_ids)).all()
        if len(customers) != len(data.customer_ids):
            raise HTTPException(status_code=400, detail=t("customer_not_found", accept_lang))
        feedback.customers = customers
    db.commit()
    db.refresh(feedback)

    old_topic_id = feedback.topic_id
    if "topic_id" in update_data and update_data["topic_id"] != old_topic_id:
        invalidate_topic_count(old_topic_id)
        invalidate_topic_count(update_data["topic_id"])
    invalidate_all_topic_counts()

    return db.query(Feedback).options(
        joinedload(Feedback.customers), joinedload(Feedback.status_changes)
    ).filter(Feedback.id == feedback_id).first()


@router.delete("/{feedback_id}", status_code=204)
def delete_feedback(
    feedback_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_delete_user),
):
    accept_lang = request.headers.get("accept-language")
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail=t("feedback_not_found", accept_lang))
    topic_id = feedback.topic_id
    db.query(StatusChange).filter(StatusChange.feedback_id == feedback_id).delete(synchronize_session="fetch")
    db.delete(feedback)
    db.commit()
    invalidate_topic_count(topic_id)


@router.post("/{feedback_id}/status-changes", response_model=StatusChangeOut, status_code=201)
def change_feedback_status(
    feedback_id: int,
    data: StatusChangeCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_status_change_user),
):
    accept_lang = request.headers.get("accept-language")
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail=t("feedback_not_found", accept_lang))
    old_status = feedback.status
    change = StatusChange(
        feedback_id=feedback_id,
        old_status=old_status,
        new_status=data.new_status,
        changed_by=user.username or user.user_id,
        remark=data.remark,
    )
    feedback.status = data.new_status
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


@router.get("/{feedback_id}/status-changes", response_model=List[StatusChangeOut])
def list_status_changes(
    feedback_id: int,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: UserIdentity = Depends(require_user),
):
    accept_lang = request.headers.get("accept-language")
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail=t("feedback_not_found", accept_lang))
    return (
        db.query(StatusChange)
        .filter(StatusChange.feedback_id == feedback_id)
        .order_by(StatusChange.changed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
