"""Trending 仓库 API 端点 - 集成硬过滤引擎。"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Header, Query

from ..domain.hard_filter import hard_filter_engine
from ..github_client import fetch_trending_repos
from ..models import RepoDto, SincePeriod

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api/v1/repos", tags=["repos"])


@router.get("/trending", response_model=List[RepoDto])
async def get_trending_repos(
    language: Optional[str] = Query(None, description="编程语言筛选"),
    stars_min: Optional[int] = Query(None, ge=0, description="最低星标数"),
    since: SincePeriod = Query(SincePeriod.WEEKLY, description="时间范围: daily/weekly/monthly"),
    limit: int = Query(100, ge=1, le=100, description="最大返回数量"),
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
) -> List[RepoDto]:
    """
    获取 GitHub Trending 仓库列表。
    
    服务端执行以下处理：
    1. 从 GitHub API 获取原始数据
    2. 应用硬过滤引擎排除不兼容/低质量项目
    3. 按星标数降序排序
    4. 返回过滤后的结果
    
    硬过滤规则：
    - 描述长度 > 10 字符
    - 星标数 >= stars_min
    - topic 不含归档/试验性关键词
    - 仓库名不含黑名单模式
    """
    logger.info(
        f"获取 Trending: language={language}, stars_min={stars_min}, "
        f"since={since.value}, limit={limit}, device={x_device_id}"
    )
    
    # 从 GitHub API 获取数据
    raw_repos = await fetch_trending_repos(
        language=language,
        stars_min=stars_min,
        since=since,
        limit=limit,
    )
    
    # 应用硬过滤引擎
    filtered_repos = hard_filter_engine.filter_and_sort(
        raw_repos,
        stars_min=stars_min,
    )
    
    # 返回指定数量上限
    result = filtered_repos[:limit]
    logger.info(f"返回 {len(result)} 个仓库（过滤前: {len(raw_repos)}）")
    
    return result
