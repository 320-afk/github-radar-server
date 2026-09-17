"""AI 分析 Prompt 模板。"""

# Allen 硬件环境画像
ALLEN_ENV_PROFILE = """
## Allen 硬件环境
- CPU: Intel i5-4210U (2核4线程, 1.7GHz)
- RAM: 7.7GB (可用约4GB)
- GPU: NVIDIA GTX 850M (4GB VRAM, CUDA 13.0)
- OS: Ubuntu 22.04 LTS

## 评估标准
1. 兼容性评分 (0-100):
   - 100: Python/Node.js/Go 等轻量级语言，无 GPU 依赖
   - 80: 可容器化，资源需求低
   - 60: 需要较多依赖但可优化
   - 40: 内存或计算密集型，需优化
   - 20: 基本无法在当前环境运行

2. 推荐理由应包含:
   - 项目核心价值
   - 与 Allen 环境的匹配度
   - 潜在学习/使用价值
"""


def build_project_analysis_prompt(
    repo_url: str,
    readme_content: str,
    dependencies: dict[str, str],
    has_dockerfile: bool,
) -> str:
    """构建项目分析 Prompt。"""
    dep_str = "\n".join([f"  - {path}: {content[:200]}" for path, content in dependencies.items()])
    docker_info = "存在" if has_dockerfile else "不存在"
    
    return f"""你是一个专业的 GitHub 项目分析师。请分析以下开源项目，输出结构化的中文评估。

{ALLEN_ENV_PROFILE}

## 待分析项目
URL: {repo_url}

## README 内容
{readme_content[:5000]}

## 依赖文件
{dep_str if dep_str else "无依赖文件信息"}

## Dockerfile
{docker_info}

## 输出格式要求
请严格按以下 JSON 格式输出，不要输出其他内容：

```json
{{
  "summary_zh": "项目的中文摘要，100-300字",
  "recommended_reasons": [
    "推荐理由1",
    "推荐理由2",
    "推荐理由3"
  ],
  "risks": [
    "风险1（如果没有风险则为空数组）"
  ],
  "compatibility_score": 85,
  "tech_stack": ["Python", "FastAPI", "Docker"]
}}
```

请分析并输出 JSON："""


def build_batch_analysis_prompt(repos: list[dict]) -> str:
    """构建批量项目分析 Prompt。"""
    repo_list = "\n".join([
        f"{i+1}. {r.get('repo_id', r.get('repo_url', 'unknown'))} | "
        f"语言:{r.get('language', 'N/A')} | "
        f"星标:{r.get('stars', 0)} | "
        f"{r.get('description', '')[:100]}"
        for i, r in enumerate(repos[:20])
    ])
    
    return f"""你是一个专业的 GitHub 项目推荐助手。

{ALLEN_ENV_PROFILE}

## 用户偏好
请根据用户画像选择最相关的项目。

## 待筛选项目列表
{repo_list}

## 输出要求
请从以上列表中选择最推荐的 5-10 个项目，输出 JSON：

```json
{{
  "selections": [
    {{
      "repo_id": "owner/repo",
      "summary_zh": "简短中文摘要",
      "recommended_reasons": ["理由1", "理由2"],
      "risks": [],
      "compatibility_score": 85,
      "tech_stack": ["Python"]
    }}
  ]
}}
```

请输出 JSON："""
