"""Pydantic models for GitHub Radar API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SincePeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RepoDto(BaseModel):
    """GitHub repository DTO returned to Android client."""

    repo_id: str = Field(..., description="Full name: owner/repo")
    name: str
    owner: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    topics: List[str] = Field(default_factory=list)
    pushed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    html_url: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class AiCuratedRequest(BaseModel):
    """Request body for AI-curated repo selection."""

    repos: List[RepoDto]
    user_profile_id: str
    limit: int = Field(default=10, ge=1, le=50)


class AiCuratedResponse(BaseModel):
    """Response with AI-curated repo IDs."""

    selected: List[str] = Field(
        default_factory=list,
        description="List of selected repo_ids (owner/repo format)"
    )
    model: str = "miniMax-m3"


class FeedbackLogEntry(BaseModel):
    """Feedback log entry."""
    repo_id: str
    action: str
    timestamp: str


class InterestVector(BaseModel):
    """User interest vector."""
    language_weights: Dict[str, float] = Field(default_factory=dict)
    topic_weights: Dict[str, float] = Field(default_factory=dict)
    feedback_counts: Dict[str, int] = Field(default_factory=dict)


class UserProfileDto(BaseModel):
    """Device user profile stored on server."""

    device_id: str
    preferred_languages: List[str] = Field(default_factory=list)
    preferred_topics: List[str] = Field(default_factory=list)
    liked_repos: List[str] = Field(default_factory=list)
    skipped_repos: List[str] = Field(default_factory=list)
    saved_repos: List[str] = Field(default_factory=list)
    feedback_log: List[FeedbackLogEntry] = Field(default_factory=list)
    interest_vector: InterestVector = Field(default_factory=InterestVector)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FeedbackDto(BaseModel):
    """User feedback payload from Android client."""

    repo_id: str
    action: str = Field(..., pattern="^(like|skip|save|TRIED|DEPLOYED|NOT_INTERESTED|TOO_MANY|TOO_FEW)$")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AckDto(BaseModel):
    """Acknowledgement response."""

    ok: bool = True
    message: str = "Feedback recorded"
