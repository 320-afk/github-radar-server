"""In-memory user profile store with async JSON file persistence."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel

from .interest_engine import compute_interest_vector


class ProfileRecord(BaseModel):
    """Internal profile record format for JSON serialization."""
    device_id: str
    preferred_languages: list[str] = []
    preferred_topics: list[str] = []
    liked_repos: list[str] = []
    skipped_repos: list[str] = []
    saved_repos: list[str] = []
    feedback_log: list[dict] = []
    interest_vector: dict = {"language_weights": {}, "topic_weights": {}, "feedback_counts": {}}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileStore:
    """Async-aware in-memory profile store with JSON file persistence."""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = os.getenv("PROFILE_STORE_PATH", ".profiles.json")
        self._path = Path(storage_path)
        self._profiles: Dict[str, ProfileRecord] = {}
        self._lock = asyncio.Lock()
        self._save_pending = False
        self._loop = None
        self._load_sync()

    def _load_sync(self) -> None:
        """Load profiles from disk (sync, called at init)."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for device_id, data in raw.items():
                    self._profiles[device_id] = ProfileRecord(**data)
            except (json.JSONDecodeError, Exception):
                pass

    async def _save_async(self) -> None:
        """Persist all profiles to disk asynchronously."""
        data = {
            device_id: profile.model_dump()
            for device_id, profile in self._profiles.items()
        }
        tmp = self._path.with_suffix(".tmp")
        # Write to tmp file, then atomic rename
        content = json.dumps(data, indent=2, ensure_ascii=False)
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: (tmp.write_text(content, encoding="utf-8"), tmp.rename(self._path))
        )

    def get_or_create(self, device_id: str) -> ProfileRecord:
        """Return existing profile or create a new one (sync, for FastAPI)."""
        if device_id not in self._profiles:
            now = datetime.utcnow().isoformat() + "Z"
            self._profiles[device_id] = ProfileRecord(
                device_id=device_id,
                created_at=now,
                updated_at=now,
            )
            # Schedule background save without blocking
            asyncio.create_task(self._save_async())
        return self._profiles[device_id]

    def record_feedback(self, device_id: str, repo_id: str, action: str) -> ProfileRecord:
        """Record a user feedback action on a repo (sync, for FastAPI)."""
        profile = self.get_or_create(device_id)
        now = datetime.utcnow().isoformat() + "Z"

        if action == "like":
            if repo_id not in profile.liked_repos:
                profile.liked_repos.append(repo_id)
            if repo_id in profile.skipped_repos:
                profile.skipped_repos.remove(repo_id)
        elif action == "skip":
            if repo_id not in profile.skipped_repos:
                profile.skipped_repos.append(repo_id)
            if repo_id in profile.liked_repos:
                profile.liked_repos.remove(repo_id)
        elif action == "save":
            if repo_id not in profile.saved_repos:
                profile.saved_repos.append(repo_id)

        # Update feedback log
        profile.feedback_log.append({
            "repo_id": repo_id,
            "action": action,
            "timestamp": now,
        })
        
        # Update interest vector
        profile.interest_vector = compute_interest_vector(profile.feedback_log)

        profile.updated_at = now
        asyncio.create_task(self._save_async())
        return profile


# Global profile store instance
profile_store = ProfileStore()
