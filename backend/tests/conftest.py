"""Shared test fixtures using an in-memory SQLite override."""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.auth import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Candidate, User

TEST_DB_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    user = User(
        id=uuid4(),
        email="admin@test.com",
        hashed_password=hash_password("password"),
        full_name="Test Admin",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def reviewer_user(db_session: AsyncSession):
    user = User(
        id=uuid4(),
        email="reviewer@test.com",
        hashed_password=hash_password("password"),
        full_name="Test Reviewer",
        role="reviewer",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_reviewer(db_session: AsyncSession):
    user = User(
        id=uuid4(),
        email="reviewer2@test.com",
        hashed_password=hash_password("password"),
        full_name="Second Reviewer",
        role="reviewer",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_candidate(db_session: AsyncSession):
    candidate = Candidate(
        id=uuid4(),
        name="John Doe",
        email="john@example.com",
        role_applied="Backend Engineer",
        skills=["Python", "FastAPI"],
        status="new",
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


@pytest_asyncio.fixture
async def admin_client(admin_user):
    token = create_access_token(admin_user.id, admin_user.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest_asyncio.fixture
async def reviewer_client(reviewer_user):
    token = create_access_token(reviewer_user.id, reviewer_user.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest_asyncio.fixture
async def second_reviewer_client(second_reviewer):
    token = create_access_token(second_reviewer.id, second_reviewer.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
