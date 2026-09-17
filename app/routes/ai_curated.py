"""AI 精选 API 端点 - 基于 MiniMax M3 的项目分析。"""
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from ..models import (
    AiCuratedRequest,
    AiCuratedResponse,
    AiDetailRequest,
    AiBatchAnalyzeResponse,
    AiCurationResultDto,
)
from ..services.ai_curation_service import curation_service
from ..services.minimax_client import MiniMaxClient
from ..cache import github_cache

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api/v1/repos", tags=["ai-curated"])


@router.post("/ai-curated", response_model=AiCuratedResponse)
async def get_ai_curated(
    request: AiCuratedRequest,
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
) -> AiCuratedResponse:
    """
    使用 MiniMax M3 AI 为用户精选仓库。
    
    若未配置 MINIMAX_API_KEY，则降级为按星标排序。
    """
    client = MiniMaxClient()
    if not client.is_configured():
        logger.info("MiniMax API Key 未配置，降级为星标排序")
        return _fallback_by_stars(request)

    # 转换为 dict 列表供批量分析
    repos_data = [r.model_dump() for r in request.repos]
    
    # 批量分析
    results = await curation_service.analyze_batch(repos_data)
    
    # 按兼容性评分排序，返回 top N
    sorted_results = sorted(results, key=lambda r: r.compatibility_score, reverse=True)
    selected = [r.repo_url for r in sorted_results[:request.limit] if r.repo_url]
    
    logger.info(f"AI 精选完成: {len(selected)} 个项目")
    return AiCuratedResponse(selected=selected, model="MiniMax-Text-01")


@router.post("/ai-detail", response_model=AiCurationResultDto)
async def get_ai_detail(
    request: AiDetailRequest,
) -> AiCurationResultDto:
    """
    获取单个项目的 AI 详细分析。
    
    包含中文摘要、推荐理由、风险提示和兼容性评分。
    """
    # 检查缓存
    cache_key = f"ai_detail:{request.repo_url}"
    cached = github_cache.get(cache_key)
    if cached:
        logger.info(f"AI 详情命中缓存: {request.repo_url}")
        return AiCurationResultDto(**cached)
    
    # 执行分析
    result = await curation_service.analyze_project(
        repo_url=request.repo_url,
        readme_content=request.readme_content or "",
        dependencies=request.dependencies or {},
        has_dockerfile=request.has_dockerfile,
    )
    
    # 缓存结果 (TTL = 6小时)
    github_cache.set(cache_key, result.to_dict(), ttl=21600)
    
    return AiCurationResultDto(**result.to_dict())


@router.post("/ai-batch-analyze", response_model=AiBatchAnalyzeResponse)
async def batch_analyze_repos(
    repos: list[AiDetailRequest],
) -> AiBatchAnalyzeResponse:
    """
    批量分析多个项目的 AI 精选结果。
    
    最多支持 20 个项目，返回每个项目的详细分析。
    """
    if len(repos) > 20:
        raise HTTPException(status_code=400, detail="最多支持 20 个项目")
    
    results = []
    for req in repos:
        result = await curation_service.analyze_project(
            repo_url=req.repo_url,
            readme_content=req.readme_content or "",
            dependencies=req.dependencies or {},
            has_dockerfile=req.has_dockerfile,
        )
        results.append(AiCurationResultDto(**result.to_dict()))
    
    return AiBatchAnalyzeResponse(
        results=results,
        model="MiniMax-Text-01",
        analyzed_count=len(results),
    )


def _fallback_by_stars(request: AiCuratedRequest) -> AiCuratedResponse:
    """降级方案：按星标数排序选择仓库。"""
    sorted_repos = sorted(request.repos, key=lambda r: r.stars, reverse=True)
    selected = [r.repo_id for r in sorted_repos[: request.limit]]
    return AiCuratedResponse(selected=selected, model="fallback-stars")
