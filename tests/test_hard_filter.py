"""硬过滤引擎测试。"""

import pytest

from app.domain.hard_filter import HardFilterEngine, hard_filter_engine
from app.models import RepoDto


def make_repo(
    repo_id: str,
    description: str | None = "A great project description",
    stars: int = 100,
    topics: list[str] | None = None,
    name: str | None = None,
) -> RepoDto:
    """创建测试用 RepoDto。"""
    if name is None:
        name = repo_id.split("/")[1]
    return RepoDto(
        repo_id=repo_id,
        name=name,
        owner=repo_id.split("/")[0],
        description=description,
        stars=stars,
        topics=topics or [],
        html_url=f"https://github.com/{repo_id}",
    )


class TestHardFilterEngine:
    def test_passes_with_good_repo(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/good-repo", "A great project with description", 100)]
        result = engine.filter_repos(repos, stars_min=50)
        assert len(result) == 1
        assert result[0].repo_id == "owner/good-repo"

    def test_rejects_short_description(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/bad-repo", "short")]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_rejects_no_description(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/no-desc-repo", None)]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_rejects_low_stars(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/low-stars", "A great project description", 10)]
        result = engine.filter_repos(repos, stars_min=50)
        assert len(result) == 0

    def test_rejects_archived_topic(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/archived-repo", "An archived project", 100, topics=["archive"])]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_rejects_experimental_topic(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/exp-repo", "An experimental project", 100, topics=["experimental"])]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_rejects_readme_name(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/readme", "A README file", 100, name="readme")]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_rejects_starter_name(self):
        engine = HardFilterEngine()
        repos = [make_repo("owner/starter", "A starter template", 100, name="my-starter")]
        result = engine.filter_repos(repos)
        assert len(result) == 0

    def test_filter_and_sort_orders_by_stars(self):
        engine = HardFilterEngine()
        repos = [
            make_repo("owner/low", "A project description here", 50),
            make_repo("owner/high", "A project description here", 500),
            make_repo("owner/medium", "A project description here", 200),
        ]
        result = engine.filter_and_sort(repos)
        assert [r.stars for r in result] == [500, 200, 50]

    def test_empty_input_returns_empty(self):
        engine = HardFilterEngine()
        result = engine.filter_repos([])
        assert result == []

    def test_global_instance_works(self):
        """验证全局 hard_filter_engine 实例可用。"""
        repos = [make_repo("owner/test", "A great project", 100)]
        result = hard_filter_engine.filter_repos(repos)
        assert len(result) == 1

    def test_topics_case_insensitive(self):
        """Topic 黑名单应大小写不敏感。"""
        engine = HardFilterEngine()
        repos = [make_repo("owner/test", "A test project", 100, topics=["ARCHIVE"])]
        result = engine.filter_repos(repos)
        assert len(result) == 0
