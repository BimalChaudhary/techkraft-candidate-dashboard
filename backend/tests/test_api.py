"""API tests covering candidate CRUD, auth enforcement, and role-based access."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_candidate_as_admin(admin_client, admin_user):
    """Admin should be able to create a candidate and receive a 201 response."""
    response = await admin_client.post(
        "/api/candidates",
        json={
            "name": "Test Candidate",
            "email": "test.candidate@example.com",
            "role_applied": "Frontend Engineer",
            "skills": ["React", "TypeScript"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Candidate"
    assert data["email"] == "test.candidate@example.com"
    assert data["status"] == "new"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_candidate_as_reviewer_forbidden(reviewer_client):
    """Reviewers should NOT be able to create candidates (403 Forbidden)."""
    response = await reviewer_client.post(
        "/api/candidates",
        json={
            "name": "Should Fail",
            "email": "fail@example.com",
            "role_applied": "Engineer",
            "skills": [],
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_candidates(admin_client, sample_candidate):
    """Listing candidates should return paginated results."""
    response = await admin_client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_get_candidate_detail(admin_client, sample_candidate):
    """Fetching a candidate by ID should return the full detail."""
    response = await admin_client.get(f"/api/candidates/{sample_candidate.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert "scores" in data
    assert "summaries" in data


@pytest.mark.asyncio
async def test_submit_score(reviewer_client, sample_candidate, reviewer_user):
    """A reviewer should be able to submit a score for a candidate."""
    response = await reviewer_client.post(
        f"/api/candidates/{sample_candidate.id}/scores",
        json={"category": "Technical Skills", "score": 4, "note": "Strong Python skills"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 4
    assert data["category"] == "Technical Skills"
    assert data["reviewer_id"] == str(reviewer_user.id)


@pytest.mark.asyncio
async def test_reviewer_cannot_see_other_reviewers_scores(
    reviewer_client, second_reviewer_client, sample_candidate, reviewer_user, second_reviewer
):
    """A reviewer should only see their own scores, not scores from other reviewers."""
    await reviewer_client.post(
        f"/api/candidates/{sample_candidate.id}/scores",
        json={"category": "Communication", "score": 5, "note": "Excellent"},
    )

    await second_reviewer_client.post(
        f"/api/candidates/{sample_candidate.id}/scores",
        json={"category": "Problem Solving", "score": 3, "note": "Average"},
    )

    response = await reviewer_client.get(f"/api/candidates/{sample_candidate.id}")
    assert response.status_code == 200
    data = response.json()
    for score in data["scores"]:
        assert score["reviewer_id"] == str(reviewer_user.id)

    response2 = await second_reviewer_client.get(f"/api/candidates/{sample_candidate.id}")
    data2 = response2.json()
    for score in data2["scores"]:
        assert score["reviewer_id"] == str(second_reviewer.id)


@pytest.mark.asyncio
async def test_admin_sees_all_scores(
    admin_client, reviewer_client, second_reviewer_client, sample_candidate
):
    """Admin should see scores from ALL reviewers."""
    await reviewer_client.post(
        f"/api/candidates/{sample_candidate.id}/scores",
        json={"category": "Technical Skills", "score": 4},
    )
    await second_reviewer_client.post(
        f"/api/candidates/{sample_candidate.id}/scores",
        json={"category": "Communication", "score": 3},
    )

    response = await admin_client.get(f"/api/candidates/{sample_candidate.id}")
    data = response.json()
    assert len(data["scores"]) >= 2


@pytest.mark.asyncio
async def test_reviewer_cannot_see_internal_notes(reviewer_client, sample_candidate):
    """Reviewers should not see internal_notes."""
    response = await reviewer_client.get(f"/api/candidates/{sample_candidate.id}")
    data = response.json()
    assert data["internal_notes"] is None


@pytest.mark.asyncio
async def test_registration_hardcodes_reviewer_role():
    """Registration must always set role to 'reviewer' regardless of input."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "testpass123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "reviewer"


@pytest.mark.asyncio
async def test_unauthenticated_access_denied():
    """Endpoints should return 403 for unauthenticated requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates")
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_soft_delete_candidate(admin_client, sample_candidate):
    """Deleting a candidate should soft-delete (not remove from DB)."""
    response = await admin_client.delete(f"/api/candidates/{sample_candidate.id}")
    assert response.status_code == 204

    response = await admin_client.get(f"/api/candidates/{sample_candidate.id}")
    assert response.status_code == 404
