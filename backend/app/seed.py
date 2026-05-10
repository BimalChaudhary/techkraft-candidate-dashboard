"""Seed script to populate the database with an admin user and sample candidates."""

import asyncio
import uuid
from datetime import datetime, timezone

from app.auth import hash_password
from app.database import Base, engine, async_session
from app.models import Candidate, Score, User


SAMPLE_CANDIDATES = [
    {"name": "Alice Johnson", "email": "alice@example.com", "role_applied": "Frontend Engineer", "skills": ["React", "TypeScript", "CSS", "Next.js"], "status": "new"},
    {"name": "Bob Smith", "email": "bob@example.com", "role_applied": "Backend Engineer", "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"], "status": "reviewed"},
    {"name": "Carol Williams", "email": "carol@example.com", "role_applied": "Full Stack Engineer", "skills": ["React", "Node.js", "PostgreSQL", "AWS"], "status": "new"},
    {"name": "David Brown", "email": "david@example.com", "role_applied": "DevOps Engineer", "skills": ["Docker", "Kubernetes", "Terraform", "AWS"], "status": "hired"},
    {"name": "Eva Martinez", "email": "eva@example.com", "role_applied": "Frontend Engineer", "skills": ["Vue.js", "JavaScript", "SCSS", "Figma"], "status": "new"},
    {"name": "Frank Lee", "email": "frank@example.com", "role_applied": "Backend Engineer", "skills": ["Go", "PostgreSQL", "gRPC", "Redis"], "status": "rejected"},
    {"name": "Grace Kim", "email": "grace@example.com", "role_applied": "Full Stack Engineer", "skills": ["React", "Python", "Django", "PostgreSQL"], "status": "reviewed"},
    {"name": "Henry Chen", "email": "henry@example.com", "role_applied": "Data Engineer", "skills": ["Python", "Spark", "Airflow", "SQL"], "status": "new"},
    {"name": "Iris Patel", "email": "iris@example.com", "role_applied": "Frontend Engineer", "skills": ["React", "TypeScript", "GraphQL", "Tailwind"], "status": "new"},
    {"name": "Jack Wilson", "email": "jack@example.com", "role_applied": "Backend Engineer", "skills": ["Java", "Spring Boot", "PostgreSQL", "Kafka"], "status": "reviewed"},
]

CATEGORIES = ["Technical Skills", "Communication", "Problem Solving", "Culture Fit", "Leadership"]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        existing = await session.execute(
            __import__("sqlalchemy").select(User).where(User.email == "admin@techkraft.com")
        )
        if existing.scalar_one_or_none():
            print("Database already seeded.")
            return

        admin = User(
            email="admin@techkraft.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            role="admin",
        )
        reviewer = User(
            email="reviewer@techkraft.com",
            hashed_password=hash_password("reviewer123"),
            full_name="Jane Reviewer",
            role="reviewer",
        )
        session.add_all([admin, reviewer])
        await session.flush()

        candidates = []
        for data in SAMPLE_CANDIDATES:
            c = Candidate(**data)
            session.add(c)
            candidates.append(c)
        await session.flush()

        import random
        for c in candidates:
            num_scores = random.randint(1, 4)
            chosen_cats = random.sample(CATEGORIES, num_scores)
            for cat in chosen_cats:
                score = Score(
                    candidate_id=c.id,
                    category=cat,
                    score=random.randint(2, 5),
                    reviewer_id=random.choice([admin.id, reviewer.id]),
                    note=f"Assessment for {cat.lower()}",
                )
                session.add(score)

        await session.commit()
        print("Database seeded successfully!")
        print(f"  Admin:    admin@techkraft.com / admin123")
        print(f"  Reviewer: reviewer@techkraft.com / reviewer123")
        print(f"  Candidates: {len(candidates)}")


if __name__ == "__main__":
    asyncio.run(seed())
