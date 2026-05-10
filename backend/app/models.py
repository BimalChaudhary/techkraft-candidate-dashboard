"""SQLAlchemy ORM models for candidates, scores, users, and summaries."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.types import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses CHAR(36) for all backends."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="reviewer")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    scores = relationship("Score", back_populates="reviewer")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role_applied = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="new")
    skills = Column(JSON, default=[])
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="candidate", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_candidates_status", "status"),
        Index("ix_candidates_role_applied", "role_applied"),
        Index("ix_candidates_deleted_at", "deleted_at"),
    )


class Score(Base):
    __tablename__ = "scores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(GUID(), ForeignKey("candidates.id"), nullable=False)
    category = Column(String(255), nullable=False)
    score = Column(Integer, nullable=False)
    reviewer_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="scores")
    reviewer = relationship("User", back_populates="scores")

    __table_args__ = (
        Index("ix_scores_candidate_id", "candidate_id"),
        Index("ix_scores_reviewer_id", "reviewer_id"),
    )


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(GUID(), ForeignKey("candidates.id"), nullable=False)
    content = Column(Text, nullable=False)
    average_score = Column(Float, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="summaries")
