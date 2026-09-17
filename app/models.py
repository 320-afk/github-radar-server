"""Pydantic models for GitHub Radar API."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

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


class AiCurationResultDto(BaseModel):
    """AI 精选结果 DTO - 包含中文摘要和推荐理由。"""

    repo_url: str = Field(..., description="仓库 URL")
    summary_zh: str = Field(..., description="中文摘要")
    recommended_reasons: List[str] = Field(default_factory=list, description="推荐理由列表")
    risks: List[str] = Field(default_factory=list, description="风险提示列表")
    compatibility_score: float = Field(..., ge=0, le=100, description="兼容性评分 0-100")
    tech_stack: List[str] = Field(default_factory=list, description="识别的技术栈")
    analyzed_at: str = Field(..., description="分析时间 ISO 格式")


class AiDetailRequest(BaseModel):
    """AI 详细分析请求。"""

    repo_url: str
    readme_content: Optional[str] = None
    dependencies: Optional[dict[str, str]] = None
    has_dockerfile: bool = False


class AiBatchAnalyzeResponse(BaseModel):
    """批量 AI 分析响应。"""

    results: List[AiCurationResultDto]
    model: str = "MiniMax-Text-01"
    analyzed_count: int


class UserProfileDto(BaseModel):
    """Device user profile stored on server."""

    device_id: str
    preferred_languages: List[str] = Field(default_factory=list)
    preferred_topics: List[str] = Field(default_factory=list)
    liked_repos: List[str] = Field(default_factory=list)
    skipped_repos: List[str] = Field(default_factory=list)
    saved_repos: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FeedbackDto(BaseModel):
    """User feedback payload from Android client."""

    repo_id: str
    action: str = Field(..., pattern="^(like|skip|save)$")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AckDto(BaseModel):
    """Acknowledgement response."""

    ok: bool = True
    message: str = "Feedback recorded"
