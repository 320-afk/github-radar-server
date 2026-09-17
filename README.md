# GitHub Radar Server

FastAPI 本地后端服务，为 GitHub Radar Android App 提供数据采集、缓存和 AI 精选能力。

## 功能

- **/health** — 健康检查端点，返回 200
- **GitHub API 缓存** — 5 分钟 TTL 内存缓存，减少 API 调用
- **设备画像** — 记录用户偏好语言、Topic、收藏和反馈
- **AI 精选代理** — MiniMax M3 个性化推荐（fallback 到 star 排序）

## 快速启动

```bash
./start.sh
```

服务器启动在 `http://0.0.0.0:8080`。

## 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub PAT，用于提高 API 速率限制 | 否 |
| `MINIMAX_API_KEY` | MiniMax API Key，用于 AI 精选 | 否 |
| `PROFILE_STORE_PATH` | 画像存储路径 | 否 |

## API 端点

```
GET  /health
GET  /api/v1/repos/trending?language=&stars_min=&since=weekly
POST /api/v1/repos/ai-curated
GET  /api/v1/user-profile/{device_id}
PUT  /api/v1/user-profile/{device_id}/feedback
```

## 运行测试

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```
