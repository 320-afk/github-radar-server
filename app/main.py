"""GitHub Radar Server - FastAPI backend for GitHub Radar Android App.

Endpoints:
  GET  /health                        - Health check
  GET  /api/v1/repos/trending         - Fetch filtered trending repos from GitHub
  POST /api/v1/repos/ai-curated       - AI-curated repo selection (MiniMax proxy)
  GET  /api/v1/user-profile/{deviceId} - Get or create device profile
  PUT  /api/v1/user-profile/{deviceId}/feedback - Record user feedback
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache import github_cache
from .data.device_profile import device_profile
from .routes import ai_curated, profile, repos

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="GitHub Radar Server",
    description="Local backend for GitHub Radar Android App",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(repos.router)
app.include_router(ai_curated.router)
app.include_router(profile.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Return 200 if the server is running."""
    return {
        "status": "ok",
        "cache_size": github_cache.size,
        "server": "github-radar-server",
        "device_profile": {
            "hostname": device_profile.hostname,
            "cpu_count": device_profile.cpu_count,
            "memory_gb": device_profile.memory_total_gb,
            "is_low_end": device_profile.is_low_end_device,
        },
    }


@app.on_event("startup")
async def startup_event():
    """Run on server startup."""
    logger.info(f"GitHub Radar Server 启动完成 - {device_profile.hostname}")
    logger.info(
        f"硬件配置: CPU={device_profile.cpu_count}核, "
        f"内存={device_profile.memory_total_gb}GB, "
        f"推荐缓存大小={device_profile.get_recommended_cache_size()}"
    )
