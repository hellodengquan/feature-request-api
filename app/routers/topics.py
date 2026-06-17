from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import UserIdentity, require_user, require_write_user, require_delete_user
from app.cache import invalidate_all_topic_counts, invalidate_topic_count
from app.database import get_db
from app.i18n import t
from app.models import Topic
from app.schemas import TopicCreate, TopicUpdate, TopicOut

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/", response_model=TopicOut, status_code=201)
def create_topic(
    data: TopicCreate,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_write_user),
):
    accept_lang = request.headers.get("accept-language")
    existing = db.query(Topic).filter(Topic.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Topic name already exists: {data.name}")
    topic = Topic(**data.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    invalidate_all_topic_counts()
    return topic


@router.get("/", response_model=List[TopicOut])
def list_topics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_user),
):
    return db.query(Topic).offset(skip).limit(limit).all()


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(
    topic_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_user),
):
    accept_lang = request.headers.get("accept-language")
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail=t("topic_not_found", accept_lang))
    return topic


@router.put("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    data: TopicUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_write_user),
):
    accept_lang = request.headers.get("accept-language")
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail=t("topic_not_found", accept_lang))
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    db.commit()
    db.refresh(topic)
    invalidate_topic_count(topic_id)
    return topic


@router.delete("/{topic_id}", status_code=204)
def delete_topic(
    topic_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_delete_user),
):
    accept_lang = request.headers.get("accept-language")
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail=t("topic_not_found", accept_lang))
    db.delete(topic)
    db.commit()
    invalidate_topic_count(topic_id)
