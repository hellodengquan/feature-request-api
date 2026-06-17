from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.models import PriorityLevel, FeedbackStatus


class CustomerCreate(BaseModel):
    name: str
    company: Optional[str] = ""
    contact: Optional[str] = ""


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    contact: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    company: Optional[str] = ""
    contact: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class TopicCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TopicOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True


class StatusChangeCreate(BaseModel):
    new_status: FeedbackStatus
    changed_by: str
    remark: Optional[str] = ""

    @field_validator("changed_by")
    @classmethod
    def changed_by_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("changed_by is required for status change")
        return v


class StatusChangeOut(BaseModel):
    id: int
    feedback_id: int
    old_status: Optional[FeedbackStatus] = None
    new_status: FeedbackStatus
    changed_by: str
    remark: Optional[str] = ""
    changed_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    description: str
    impact_scope: Optional[str] = ""
    priority: Optional[PriorityLevel] = PriorityLevel.MEDIUM
    status: Optional[FeedbackStatus] = FeedbackStatus.PENDING
    source: Optional[str] = ""
    topic_id: Optional[int] = None
    customer_ids: Optional[List[int]] = []


class FeedbackUpdate(BaseModel):
    description: Optional[str] = None
    impact_scope: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    status: Optional[FeedbackStatus] = None
    source: Optional[str] = None
    topic_id: Optional[int] = None
    customer_ids: Optional[List[int]] = None
    changed_by: Optional[str] = None
    remark: Optional[str] = ""


class FeedbackOut(BaseModel):
    id: int
    description: str
    impact_scope: Optional[str] = ""
    priority: PriorityLevel
    status: FeedbackStatus
    source: Optional[str] = ""
    topic_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    customers: List[CustomerOut] = []
    status_changes: List[StatusChangeOut] = []

    class Config:
        from_attributes = True


class FeedbackListItem(BaseModel):
    id: int
    description: str
    impact_scope: Optional[str] = ""
    priority: PriorityLevel
    status: FeedbackStatus
    source: Optional[str] = ""
    topic_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackGroupByTopic(BaseModel):
    topic: Optional[TopicOut] = None
    feedbacks: List[FeedbackListItem]
    feedback_count: int = 0


class PendingEvaluationReport(BaseModel):
    total: int
    feedbacks: List[FeedbackListItem]
    timezone_offset: str = "+00:00"
