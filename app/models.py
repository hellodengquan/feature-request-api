from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.database import Base

feedback_customer = Table(
    "feedback_customer",
    Base.metadata,
    Column("feedback_id", Integer, ForeignKey("feedbacks.id"), primary_key=True),
    Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True),
)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    company = Column(String(128), default="")
    contact = Column(String(128), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    feedbacks = relationship("Feedback", secondary=feedback_customer, back_populates="customers")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    feedbacks = relationship("Feedback", back_populates="topic")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    impact_scope = Column(String(64), default="")
    priority = Column(String(16), default="medium")
    status = Column(String(32), default="pending")
    source = Column(String(32), default="")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    topic = relationship("Topic", back_populates="feedbacks")
    customers = relationship("Customer", secondary=feedback_customer, back_populates="feedbacks")
    status_changes = relationship("StatusChange", back_populates="feedback", cascade="all, delete-orphan")


class StatusChange(Base):
    __tablename__ = "status_changes"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedbacks.id"), nullable=False)
    old_status = Column(String(32), default="")
    new_status = Column(String(32), nullable=False)
    changed_by = Column(String(64), default="")
    remark = Column(Text, default="")
    changed_at = Column(DateTime, default=datetime.utcnow)

    feedback = relationship("Feedback", back_populates="status_changes")
