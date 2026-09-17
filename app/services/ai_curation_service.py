"""AI 精选服务 - 基于 MiniMax M3 的项目分析。"""
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from .minimax_client import MiniMaxClient
from .prompts import build_project_analysis_prompt, build_batch_analysis_prompt

logger = logging.getLogger("uvicorn")


@dataclass
class AiCurationResult:
    """AI 精选结果数据结构。"""
    repo_url: str
    summary_zh: str
    recommended_reasons: list[str]
    risks: list[str]
    compatibility_score: float
    tech_stack: list[str]
    analyzed_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AiCurationResult":
        return cls(**data)


class CurationService:
    """AI 精选服务核心类。"""

    def __init__(self, client: Optional[MiniMaxClient] = None):
        self.client = client or MiniMaxClient()

    async def analyze_project(
        self,
        repo_url: str,
        readme_content: str,
        dependencies: Optional[dict[str, str]] = None,
        has_dockerfile: bool = False,
    ) -> AiCurationResult:
        """分析单个项目，生成 AI 精选结果。"""
        if not self.client.is_configured():
            logger.warning("MiniMax API 未配置，返回空结果")
            return self._empty_result(repo_url)

        prompt = build_project_analysis_prompt(
            repo_url=repo_url,
            readme_content=readme_content,
            dependencies=dependencies or {},
            has_dockerfile=has_dockerfile,
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.client.chat(messages, max_tokens=2048, temperature=0.3)
            
            content = response["choices"][0]["message"]["content"]
            result = self._parse_json_response(content, repo_url)
            
            logger.info(f"项目分析完成: {repo_url}, score={result.compatibility_score}")
            return result
            
        except Exception as e:
            logger.error(f"AI 分析失败: {repo_url}, error={e}")
            return self._empty_result(repo_url)

    async def analyze_batch(self, repos: list[dict]) -> list[AiCurationResult]:
        """批量分析项目。"""
        if not self.client.is_configured():
            logger.warning("MiniMax API 未配置")
            return [self._empty_result(r.get("repo_url", r.get("repo_id", ""))) for r in repos]

        prompt = build_batch_analysis_prompt(repos)

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.client.chat(messages, max_tokens=4096, temperature=0.3)
            
            content = response["choices"][0]["message"]["content"]
            results = self._parse_batch_response(content, repos)
            
            logger.info(f"批量分析完成: {len(results)} 个项目")
            return results
            
        except Exception as e:
            logger.error(f"批量分析失败: {e}")
            return [self._empty_result(r.get("repo_url", r.get("repo_id", ""))) for r in repos]

    def _parse_json_response(self, content: str, repo_url: str) -> AiCurationResult:
        """解析 AI 返回的 JSON 内容。"""
        # 尝试提取 JSON
        json_str = content.strip()
        if "```json" in json_str:
            start = json_str.find("```json") + 7
            end = json_str.rfind("```")
            json_str = json_str[start:end].strip()
        elif "```" in json_str:
            start = json_str.find("```") + 3
            end = json_str.rfind("```")
            json_str = json_str[start:end].strip()

        try:
            data = json.loads(json_str)
            return AiCurationResult(
                repo_url=repo_url,
                summary_zh=data.get("summary_zh", "暂无摘要"),
                recommended_reasons=data.get("recommended_reasons", []),
                risks=data.get("risks", []),
                compatibility_score=data.get("compatibility_score", 50),
                tech_stack=data.get("tech_stack", []),
                analyzed_at=datetime.utcnow().isoformat() + "Z",
            )
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
            return self._empty_result(repo_url)

    def _parse_batch_response(self, content: str, repos: list[dict]) -> list[AiCurationResult]:
        """解析批量分析响应。"""
        json_str = content.strip()
        if "```json" in json_str:
            start = json_str.find("```json") + 7
            end = json_str.rfind("```")
            json_str = json_str[start:end].strip()

        try:
            data = json.loads(json_str)
            selections = data.get("selections", [])
            return [
                AiCurationResult(
                    repo_url=s.get("repo_id", ""),
                    summary_zh=s.get("summary_zh", "暂无摘要"),
                    recommended_reasons=s.get("recommended_reasons", []),
                    risks=s.get("risks", []),
                    compatibility_score=s.get("compatibility_score", 50),
                    tech_stack=s.get("tech_stack", []),
                    analyzed_at=datetime.utcnow().isoformat() + "Z",
                )
                for s in selections
            ]
        except json.JSONDecodeError:
            return [self._empty_result(r.get("repo_url", r.get("repo_id", ""))) for r in repos]

    def _empty_result(self, repo_url: str) -> AiCurationResult:
        """返回空结果。"""
        return AiCurationResult(
            repo_url=repo_url,
            summary_zh="AI 分析暂时不可用",
            recommended_reasons=["星标数较高"] if repo_url else [],
            risks=["分析服务暂不可用"],
            compatibility_score=50,
            tech_stack=[],
            analyzed_at=datetime.utcnow().isoformat() + "Z",
        )


# 全局服务实例
curation_service = CurationService()
