"""Candidate CRUD, scoring, AI summary, and SSE streaming endpoints."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Candidate, Score, User
from app.schemas import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateUpdate,
    PaginatedCandidates,
    ScoreCreate,
    ScoreResponse,
    SummaryResponse,
)
from app.services.candidate_service import (
    generate_mock_summary,
    get_candidate_detail,
    list_candidates,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

# In-memory event bus for SSE score updates
_score_events: dict[UUID, list[asyncio.Queue]] = {}


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedCandidates)
async def get_candidates(
    status_filter: Optional[str] = Query(None, alias="status"),
    role_applied: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = await list_candidates(
        db,
        status=status_filter,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    candidates = []
    for c in items:
        data = CandidateResponse.model_validate(c)
        if user.role != "admin":
            data.internal_notes = None
        candidates.append(data)

    total_pages = (total + page_size - 1) // page_size
    return PaginatedCandidates(items=candidates, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    existing = await db.execute(select(Candidate).where(Candidate.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate email already exists")

    candidate = Candidate(**payload.model_dump())
    db.add(candidate)
    await db.flush()
    await db.refresh(candidate)
    return candidate


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate = await get_candidate_detail(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    scores = candidate.scores
    if user.role != "admin":
        scores = [s for s in scores if s.reviewer_id == user.id]

    score_responses = []
    for s in scores:
        sr = ScoreResponse.model_validate(s)
        if s.reviewer:
            sr.reviewer_name = s.reviewer.full_name
        score_responses.append(sr)

    result = CandidateDetailResponse.model_validate(candidate)
    result.scores = score_responses
    result.summaries = [SummaryResponse.model_validate(s) for s in candidate.summaries]
    if user.role != "admin":
        result.internal_notes = None
    return result


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: UUID,
    payload: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate = await get_candidate_detail(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "internal_notes" in update_data and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can edit internal notes")

    for field, value in update_data.items():
        setattr(candidate, field, value)

    await db.flush()
    await db.refresh(candidate)
    resp = CandidateResponse.model_validate(candidate)
    if user.role != "admin":
        resp.internal_notes = None
    return resp


# ── Soft Delete ───────────────────────────────────────────────────────────────

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    candidate = await get_candidate_detail(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    candidate.deleted_at = datetime.now(timezone.utc)
    await db.flush()


# ── Scores ────────────────────────────────────────────────────────────────────

@router.post("/{candidate_id}/scores", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def submit_score(
    candidate_id: UUID,
    payload: ScoreCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    candidate = await get_candidate_detail(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    score = Score(
        candidate_id=candidate_id,
        category=payload.category,
        score=payload.score,
        reviewer_id=user.id,
        note=payload.note,
    )
    db.add(score)
    await db.flush()
    await db.refresh(score)

    sr = ScoreResponse.model_validate(score)
    sr.reviewer_name = user.full_name

    if candidate_id in _score_events:
        event_data = json.dumps(sr.model_dump(mode="json"), default=str)
        for q in _score_events[candidate_id]:
            await q.put(event_data)

    return sr


# ── AI Summary ────────────────────────────────────────────────────────────────

@router.post("/{candidate_id}/summary", response_model=SummaryResponse, status_code=status.HTTP_201_CREATED)
async def trigger_summary(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        summary = await generate_mock_summary(db, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return summary


# ── SSE Stream (Stretch Goal) ─────────────────────────────────────────────────

@router.get("/{candidate_id}/stream")
async def stream_scores(
    candidate_id: UUID,
    user: User = Depends(get_current_user),
):
    queue: asyncio.Queue = asyncio.Queue()
    _score_events.setdefault(candidate_id, []).append(queue)

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield {"event": "score_update", "data": data}
        except asyncio.CancelledError:
            pass
        finally:
            _score_events.get(candidate_id, []).remove(queue)

    return EventSourceResponse(event_generator())
