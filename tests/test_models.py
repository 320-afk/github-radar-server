"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models import (
    AiCuratedRequest,
    AiCuratedResponse,
    FeedbackDto,
    RepoDto,
    SincePeriod,
    UserProfileDto,
)


class TestRepoDto:
    def test_full_construction(self):
        repo = RepoDto(
            repo_id="octocat/Hello-World",
            name="Hello-World",
            owner="octocat",
            description="A hello world repo",
            language="Python",
            stars=100,
            forks=10,
            open_issues=2,
            watchers=50,
            topics=["hello-world"],
            html_url="https://github.com/octocat/Hello-World",
        )
        assert repo.repo_id == "octocat/Hello-World"
        assert repo.stars == 100

    def test_minimal_construction(self):
        repo = RepoDto(
            repo_id="octocat/Hello-World",
            name="Hello-World",
            owner="octocat",
            html_url="https://github.com/octocat/Hello-World",
        )
        assert repo.language is None
        assert repo.stars == 0


class TestSincePeriod:
    def test_enum_values(self):
        assert SincePeriod.DAILY.value == "daily"
        assert SincePeriod.WEEKLY.value == "weekly"
        assert SincePeriod.MONTHLY.value == "monthly"


class TestFeedbackDto:
    def test_valid_actions(self):
        for action in ["like", "skip", "save", "TRIED", "DEPLOYED", "NOT_INTERESTED", "TOO_MANY", "TOO_FEW"]:
            fb = FeedbackDto(repo_id="octocat/repo", action=action)
            assert fb.action == action

    def test_invalid_action_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackDto(repo_id="octocat/repo", action="invalid")

    def test_default_timestamp(self):
        fb = FeedbackDto(repo_id="octocat/repo", action="like")
        assert fb.timestamp.endswith("Z")


class TestAiCuratedRequest:
    def test_construction(self):
        repos = [
            RepoDto(
                repo_id="octocat/repo1",
                name="repo1",
                owner="octocat",
                html_url="https://github.com/octocat/repo1",
            )
        ]
        req = AiCuratedRequest(repos=repos, user_profile_id="device-123", limit=5)
        assert len(req.repos) == 1
        assert req.limit == 5


class TestAiCuratedResponse:
    def test_construction(self):
        resp = AiCuratedResponse(selected=["octocat/repo1", "octocat/repo2"])
        assert len(resp.selected) == 2
        assert resp.model == "miniMax-m3"


class TestUserProfileDto:
    def test_construction(self):
        profile = UserProfileDto(
            device_id="device-abc",
            preferred_languages=["Python", "Kotlin"],
            preferred_topics=["machine-learning"],
        )
        assert profile.device_id == "device-abc"
        assert "Python" in profile.preferred_languages
