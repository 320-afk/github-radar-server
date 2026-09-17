"""用户画像 API 端点。"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..cache import repo_cache
from ..models import AckDto, FeedbackDto, RepoDto, UserProfileDto
from ..profile_store import profile_store

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api/v1/user-profile", tags=["profile"])


@router.get("/{device_id}", response_model=UserProfileDto)
async def get_user_profile(device_id: str) -> UserProfileDto:
    """
    获取或创建设备画像。
    
    根据 device_id 查询已有画像，如不存在则创建新画像。
    """
    logger.info(f"获取用户画像: device_id={device_id}")
    record = profile_store.get_or_create(device_id)
    return UserProfileDto(**record.model_dump())


@router.put("/{device_id}/feedback", response_model=UserProfileDto)
async def submit_feedback(
    device_id: str,
    feedback: FeedbackDto,
) -> UserProfileDto:
    """
    记录用户对仓库的反馈（喜欢/跳过/收藏）。
    
    反馈将用于更新用户画像，以优化后续 AI 精选推荐。
    """
    logger.info(f"记录反馈: device_id={device_id}, repo={feedback.repo_id}, action={feedback.action}")
    record = profile_store.record_feedback(device_id, feedback.repo_id, feedback.action)
    return UserProfileDto(**record.model_dump())


@router.post("/{device_id}/reset", response_model=UserProfileDto)
async def reset_profile(device_id: str) -> UserProfileDto:
    """
    重置用户画像（清除所有偏好和历史）。
    
    谨慎使用，仅在用户明确要求时调用。
    """
    logger.warning(f"重置画像: device_id={device_id}")
    # 获取现有画像后清空偏好字段
    record = profile_store.get_or_create(device_id)
    record.preferred_languages = []
    record.preferred_topics = []
    record.liked_repos = []
    record.skipped_repos = []
    record.saved_repos = []
    record.feedback_log = []
    record.interest_vector = {"language_weights": {}, "topic_weights": {}, "feedback_counts": {}}
    return UserProfileDto(**record.model_dump())


@router.get("/{device_id}/similar/{repo_id:path}", response_model=List[RepoDto])
async def get_similar_repos(
    device_id: str,
    repo_id: str,
    limit: int = Query(5, ge=1, le=50),
) -> List[RepoDto]:
    """
    Get similar repositories based on a given repository and user profile.
    """
    logger.info(f"Finding similar repos for: {repo_id}, device: {device_id}")
    
    target_repo = repo_cache.get(repo_id)
    if not target_repo:
        raise HTTPException(status_code=404, detail="Target repository not found in cache")
        
    target_topics = set(target_repo.topics)
    
    record = profile_store.get_or_create(device_id)
    interest_vector = record.interest_vector
    topic_weights = interest_vector.get("topic_weights", {})
    language_weights = interest_vector.get("language_weights", {})
    
    similarities = []
    for cached_repo_id, repo in repo_cache.items():
        if cached_repo_id == repo_id:
            continue
            
        repo_topics = set(repo.topics)
        overlap = target_topics.intersection(repo_topics)
        
        # Base similarity from topic overlap
        similarity = len(overlap)
        
        # Boost from user topic interests
        for topic in repo_topics:
            similarity += topic_weights.get(topic, 0.0)
            
        # Boost from user language interests
        if repo.language:
            similarity += language_weights.get(repo.language, 0.0)
            
        similarities.append((similarity, repo))
        
    similarities.sort(key=lambda x: x[0], reverse=True)
    return [repo for _, repo in similarities[:limit]]
