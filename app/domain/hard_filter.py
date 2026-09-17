"""硬过滤引擎 - 排除不兼容或低质量项目。"""

import logging
from typing import List, Optional

from ..models import RepoDto

logger = logging.getLogger("uvicorn")


class HardFilterEngine:
    """服务端硬过滤引擎，排除不符合质量标准的仓库。"""

    # 最低描述长度（字符）
    MIN_DESCRIPTION_LENGTH = 10

    # 被排除的 topic 关键词（用于过滤已归档/试验性项目）
    EXCLUDED_TOPICS = frozenset({
        "archive",
        "archived",
        "experimental",
        "abandoned",
        "dead",
    })

    # 仓库名黑名单（用于过滤工具脚本等）
    EXCLUDED_NAME_PATTERNS = frozenset({
        "readme",
        "template",
        "skeleton",
        "boilerplate",
        "starter",
        "-starter",
        "-template",
    })

    # 最低星标数（可配置）
    DEFAULT_MIN_STARS = 0

    def __init__(
        self,
        min_description_length: int = MIN_DESCRIPTION_LENGTH,
        min_stars: int = DEFAULT_MIN_STARS,
    ):
        self.min_description_length = min_description_length
        self.min_stars = min_stars

    def filter_repos(self, repos: List[RepoDto], stars_min: Optional[int] = None) -> List[RepoDto]:
        """
        对仓库列表应用硬过滤规则。
        
        过滤条件：
        1. 必须有描述，且长度 > min_description_length
        2. 星标数 >= stars_min（若提供）
        3. topic 不包含排除关键词
        4. 仓库名不匹配黑名单模式
        
        Args:
            repos: 原始仓库列表
            stars_min: 最低星标数（可选，覆盖默认值）
            
        Returns:
            过滤后的仓库列表
        """
        effective_min_stars = stars_min if stars_min is not None else self.min_stars
        filtered = []

        for repo in repos:
            if self._passes_filter(repo, effective_min_stars):
                filtered.append(repo)

        logger.debug(f"硬过滤: {len(repos)} -> {len(filtered)} 个仓库")
        return filtered

    def _passes_filter(self, repo: RepoDto, min_stars: int) -> bool:
        """检查单个仓库是否通过过滤。"""
        # 条件1: 描述检查
        if not repo.description or len(repo.description.strip()) <= self.min_description_length:
            logger.debug(f"排除 (描述不足): {repo.repo_id}")
            return False

        # 条件2: 星标数检查
        if repo.stars < min_stars:
            logger.debug(f"排除 (星标不足): {repo.repo_id} ({repo.stars} < {min_stars})")
            return False

        # 条件3: topic 黑名单检查
        for topic in repo.topics:
            if topic.lower() in self.EXCLUDED_TOPICS:
                logger.debug(f"排除 (topic): {repo.repo_id} (topic={topic})")
                return False

        # 条件4: 仓库名黑名单检查
        name_lower = repo.name.lower()
        for pattern in self.EXCLUDED_NAME_PATTERNS:
            if pattern in name_lower:
                logger.debug(f"排除 (名称): {repo.repo_id} (name={repo.name})")
                return False

        return True

    def filter_and_sort(
        self,
        repos: List[RepoDto],
        stars_min: Optional[int] = None,
    ) -> List[RepoDto]:
        """
        过滤后按星标数降序排序。
        
        Args:
            repos: 原始仓库列表
            stars_min: 最低星标数
            
        Returns:
            过滤并排序后的仓库列表
        """
        filtered = self.filter_repos(repos, stars_min)
        return sorted(filtered, key=lambda r: r.stars, reverse=True)


# 全局硬过滤引擎实例
hard_filter_engine = HardFilterEngine()
