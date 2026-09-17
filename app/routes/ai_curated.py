"""AI 精选 API 端点 - MiniMax M3 代理服务。"""

import logging
import os
from typing import List

import httpx

from fastapi import APIRouter, Header

from ..models import AiCuratedRequest, AiCuratedResponse
from ..profile_store import profile_store

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api/v1/repos", tags=["ai-curated"])


@router.post("/ai-curated", response_model=AiCuratedResponse)
async def get_ai_curated(
    request: AiCuratedRequest,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> AiCuratedResponse:
    """
    使用 MiniMax M3 AI 为用户精选仓库。
    
    服务端根据用户画像（偏好语言/领域）注入个性化提示词，
    调用 MiniMax API 返回精选结果。
    
    若未配置 MINIMAX_API_KEY，则降级为按星标排序。
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        logger.info("MiniMax API Key 未配置，降级为星标排序")
        return _fallback_by_stars(request)

    # 获取用户画像用于个性化
    device_id = x_device_id or request.user_profile_id
    profile = profile_store.get_or_create(device_id)
    
    # 构建个性化提示词
    langs = ", ".join(profile.preferred_languages) if profile.preferred_languages else "any"
    topics = ", ".join(profile.preferred_topics) if profile.preferred_topics else "general open source"
    
    prompt = _build_prompt(request.repos, request.limit, langs, topics)
    
    try:
        result = await _call_minimax(api_key, prompt, request.limit)
        logger.info(f"AI 精选完成: device_id={device_id}, selected={len(result.selected)} 个")
        return result
    except Exception as e:
        logger.warning(f"MiniMax API 调用失败: {e}，降级为星标排序")
        return _fallback_by_stars(request)


def _build_prompt(
    repos: List[dict],
    limit: int,
    languages: str,
    topics: str,
) -> str:
    """构建给 MiniMax 的提示词。"""
    prompt = (
        f"你是一个 GitHub 项目推荐助手。\n"
        f"用户画像 - 语言: {languages}, 领域: {topics}\n\n"
        f"从以下仓库列表中，挑选出最相关的 {limit} 个项目。\n"
        f"评分标准: 相关性、活跃度、社区影响力。\n"
        f"只返回 JSON 格式: {{\"selected\": [\"owner/repo1\", ...]}}\n\n"
        f"仓库列表:\n"
    )
    
    for r in repos:
        desc = (r.description or "").strip()
        lang = r.language or "N/A"
        stars = r.stars
        prompt += f"- {r.repo_id} | 语言:{lang} | 星标:{stars} | {desc}\n"
    
    return prompt


async def _call_minimax(api_key: str, prompt: str, limit: int) -> AiCuratedResponse:
    """调用 MiniMax API。"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.minimax.chat/v1/text/chatcompletion_v2",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "MiniMax-Text-01",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        result = resp.json()
        
        content = result["choices"][0]["message"]["content"]
        
        # 解析 JSON 响应
        import json
        try:
            parsed = json.loads(content)
            selected = parsed.get("selected", [])
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取 JSON 部分
            import re
            match = re.search(r'\{[^}]+\}', content)
            if match:
                parsed = json.loads(match.group())
                selected = parsed.get("selected", [])
            else:
                selected = []
        
        return AiCuratedResponse(
            selected=selected[:limit],
            model="MiniMax-Text-01",
        )


def _fallback_by_stars(request: AiCuratedRequest) -> AiCuratedResponse:
    """降级方案：按星标数排序选择仓库。"""
    sorted_repos = sorted(request.repos, key=lambda r: r.stars, reverse=True)
    selected = [r.repo_id for r in sorted_repos[: request.limit]]
    return AiCuratedResponse(selected=selected, model="fallback-stars")
