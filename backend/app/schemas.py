"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Candidate ─────────────────────────────────────────────────────────────────

class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role_applied: str = Field(min_length=1, max_length=255)
    skills: list[str] = Field(default_factory=list)
    status: str = Field(default="new")


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_applied: Optional[str] = None
    skills: Optional[list[str]] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None


class CandidateResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role_applied: str
    status: str
    skills: list[str]
    internal_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateDetailResponse(CandidateResponse):
    scores: list["ScoreResponse"] = []
    summaries: list["SummaryResponse"] = []


class PaginatedCandidates(BaseModel):
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Score ─────────────────────────────────────────────────────────────────────

class ScoreCreate(BaseModel):
    category: str = Field(min_length=1, max_length=255)
    score: int = Field(ge=1, le=5)
    note: Optional[str] = None


class ScoreResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    category: str
    score: int
    reviewer_id: UUID
    reviewer_name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Summary ───────────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    content: str
    average_score: Optional[float] = None
    generated_at: datetime

    model_config = {"from_attributes": True}
