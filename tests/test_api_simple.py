"""Simple endpoint tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["server"] == "github-radar-server"

    def test_health_includes_cache_size(self, client):
        response = client.get("/health")
        data = response.json()
        assert "cache_size" in data
        assert isinstance(data["cache_size"], int)


class TestUserProfileEndpoints:
    def test_get_profile_creates_new(self, client):
        import uuid
        device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.get(f"/api/v1/user-profile/{device_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_id

    def test_submit_feedback_like(self, client):
        import uuid
        device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/user-profile/{device_id}/feedback",
            json={"repo_id": "octocat/repo1", "action": "like"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "octocat/repo1" in data["liked_repos"]

    def test_submit_feedback_skip(self, client):
        import uuid
        device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/user-profile/{device_id}/feedback",
            json={"repo_id": "octocat/repo2", "action": "skip"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "octocat/repo2" in data["skipped_repos"]

    def test_submit_feedback_save(self, client):
        import uuid
        device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/user-profile/{device_id}/feedback",
            json={"repo_id": "octocat/repo3", "action": "save"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "octocat/repo3" in data["saved_repos"]

    def test_submit_feedback_invalid_action_rejected(self, client):
        import uuid
        device_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/user-profile/{device_id}/feedback",
            json={"repo_id": "octocat/repo3", "action": "dislike"},
        )
        assert response.status_code == 422  # Pydantic validation error


class TestAiCuratedEndpoint:
    def test_ai_curated_fallback_without_key(self, client, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        repos = [
            {"repo_id": "high/stars", "name": "stars", "owner": "high", "stars": 1000, "html_url": "https://github.com/high/stars"},
            {"repo_id": "low/stars", "name": "stars", "owner": "low", "stars": 100, "html_url": "https://github.com/low/stars"},
        ]
        response = client.post(
            "/api/v1/repos/ai-curated",
            json={"repos": repos, "user_profile_id": "device-abc", "limit": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "fallback-stars"
        assert data["selected"][0] == "high/stars"
        assert len(data["selected"]) <= 2

    def test_ai_curated_limit_respected(self, client, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        repos = [
            {"repo_id": f"r{i}/repo", "name": f"repo{i}", "owner": f"o{i}", "stars": 100 - i, "html_url": f"https://github.com/o{i}/repo{i}"}
            for i in range(20)
        ]
        response = client.post(
            "/api/v1/repos/ai-curated",
            json={"repos": repos, "user_profile_id": "device-x", "limit": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["selected"]) <= 3
