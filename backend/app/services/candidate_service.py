"""Business logic for candidate operations — keeps routers thin."""

import asyncio
import random
from typing import Optional
from uuid import UUID

from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.types import String

from app.models import Candidate, Score, Summary


async def list_candidates(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    role_applied: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Candidate], int]:
    """Return paginated, filtered candidates (excludes soft-deleted)."""
    page_size = min(max(page_size, 1), 50)
    page = max(page, 1)

    base = select(Candidate).where(Candidate.deleted_at.is_(None))
    count_q = select(func.count()).select_from(Candidate).where(Candidate.deleted_at.is_(None))

    if status:
        base = base.where(Candidate.status == status)
        count_q = count_q.where(Candidate.status == status)
    if role_applied:
        base = base.where(Candidate.role_applied.ilike(f"%{role_applied}%"))
        count_q = count_q.where(Candidate.role_applied.ilike(f"%{role_applied}%"))
    if skill:
        skill_filter = cast(Candidate.skills, String).ilike(f"%{skill}%")
        base = base.where(skill_filter)
        count_q = count_q.where(skill_filter)
    if keyword:
        pattern = f"%{keyword}%"
        kw_filter = or_(
            Candidate.name.ilike(pattern),
            Candidate.email.ilike(pattern),
            Candidate.role_applied.ilike(pattern),
        )
        base = base.where(kw_filter)
        count_q = count_q.where(kw_filter)

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    query = base.order_by(Candidate.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_candidate_detail(db: AsyncSession, candidate_id: UUID) -> Optional[Candidate]:
    """Fetch a single candidate with eager-loaded scores and summaries."""
    query = (
        select(Candidate)
        .options(
            selectinload(Candidate.scores).selectinload(Score.reviewer),
            selectinload(Candidate.summaries),
        )
        .where(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def generate_mock_summary(db: AsyncSession, candidate_id: UUID) -> Summary:
    """Simulate an async LLM call with a 2-second delay, then persist a summary."""
    candidate = await get_candidate_detail(db, candidate_id)
    if not candidate:
        raise ValueError("Candidate not found")

    await asyncio.sleep(2)

    scores = candidate.scores
    avg = sum(s.score for s in scores) / len(scores) if scores else 0.0
    categories = {}
    for s in scores:
        categories.setdefault(s.category, []).append(s.score)
    cat_summary = "; ".join(f"{cat}: avg {sum(v)/len(v):.1f}" for cat, v in categories.items())

    strengths = ["problem solving", "communication", "technical depth", "leadership", "adaptability"]
    chosen = random.sample(strengths, min(3, len(strengths)))

    content = (
        f"AI-Generated Assessment for {candidate.name}\n\n"
        f"Overall Score: {avg:.1f}/5.0 based on {len(scores)} review(s).\n"
        f"Category Breakdown: {cat_summary or 'No scores yet.'}\n\n"
        f"Key Strengths: {', '.join(chosen)}.\n\n"
        f"Recommendation: {'Strong hire' if avg >= 4 else 'Consider' if avg >= 3 else 'Needs further review'}. "
        f"The candidate applied for {candidate.role_applied} and demonstrates "
        f"{'excellent' if avg >= 4 else 'adequate' if avg >= 3 else 'developing'} competencies "
        f"across evaluated categories."
    )

    summary = Summary(candidate_id=candidate_id, content=content, average_score=round(avg, 2))
    db.add(summary)
    await db.flush()
    await db.refresh(summary)
    return summary
