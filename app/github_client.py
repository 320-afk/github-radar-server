"""GitHub API client with caching and rate-limit awareness."""

import os
from datetime import datetime, timedelta
from typing import List, Optional

import httpx

from .cache import github_cache
from .models import RepoDto, SincePeriod


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Radar-Server/0.1.0",
}


def _build_cache_key(prefix: str, **kwargs) -> str:
    """Build a deterministic cache key from keyword arguments."""
    parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            parts.append(f"{k}={v}")
    return "|".join(parts)


def _repo_from_github_json(data: dict) -> RepoDto:
    """Convert a GitHub API repo JSON object to RepoDto."""
    return RepoDto(
        repo_id=f"{data['owner']['login']}/{data['name']}",
        name=data.get("name", ""),
        owner=data.get("owner", {}).get("login", ""),
        description=data.get("description"),
        language=data.get("language"),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        open_issues=data.get("open_issues_count", 0),
        watchers=data.get("watchers_count", 0),
        topics=data.get("topics", []),
        pushed_at=data.get("pushed_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        html_url=data.get("html_url", ""),
        avatar_url=data.get("owner", {}).get("avatar_url"),
    )


def _since_to_date(since: SincePeriod) -> str:
    """Convert SincePeriod to a YYYY-MM-DD date string for GitHub API."""
    now = datetime.now()
    days = {
        SincePeriod.DAILY: 1,
        SincePeriod.WEEKLY: 30,
        SincePeriod.MONTHLY: 365,
    }.get(since, 30)
    return (now - timedelta(days=days)).strftime("%Y-%m-%d")


async def fetch_trending_repos(
    language: Optional[str] = None,
    stars_min: Optional[int] = None,
    since: SincePeriod = SincePeriod.WEEKLY,
    limit: int = 100,
) -> List[RepoDto]:
    """
    Fetch trending GitHub repositories using GitHub Search API.
    Results are cached for 5 minutes to reduce API calls.
    """
    cache_key = _build_cache_key(
        "trending", language=language, stars_min=stars_min, since=since.value, limit=limit
    )

    cached, age = github_cache.get_with_age(cache_key)
    if cached is not None:
        return cached

    token = os.getenv("GITHUB_TOKEN")
    headers = DEFAULT_HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    date_str = _since_to_date(since)
    query_parts = [f"created:>{date_str}"]
    if language:
        query_parts.append(f"language:{language}")
    if stars_min is not None and stars_min > 0:
        query_parts.append(f"stars:>{stars_min}")

    query = " ".join(query_parts)
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit, 100),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/search/repositories",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    repos = [_repo_from_github_json(item) for item in data.get("items", [])]
    github_cache.set(cache_key, repos)
    return repos


async def fetch_repo_details(owner: str, repo_name: str) -> Optional[RepoDto]:
    """Fetch detailed info for a single repository."""
    cache_key = _build_cache_key("repo_detail", owner=owner, repo=repo_name)
    cached = github_cache.get(cache_key)
    if cached is not None:
        return cached

    token = os.getenv("GITHUB_TOKEN")
    headers = DEFAULT_HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}",
            headers=headers,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

    repo = _repo_from_github_json(data)
    github_cache.set(cache_key, repo)
    return repo
