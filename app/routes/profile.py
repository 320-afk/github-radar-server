"""用户画像 API 端点。"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ..models import AckDto, FeedbackDto, UserProfileDto
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
    return UserProfileDto(**record.model_dump())
