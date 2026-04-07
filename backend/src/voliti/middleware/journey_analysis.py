# ABOUTME: JourneyAnalysisMiddleware — 长期旅程视角分析，定期扫描用户时间轴并注入摘要
# ABOUTME: 会话触发 + 3 天时间门槛，fail-open 设计，分析失败不阻塞 Coach

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from voliti.middleware.base import PromptInjectionMiddleware

logger = logging.getLogger(__name__)

_ANALYSIS_INTERVAL_DAYS = 3
_LAST_ANALYSIS_KEY = "/user/derived/last_journey_analysis.json"
_PATTERN_INDEX_KEY = "/user/derived/pattern_index.md"


class JourneyAnalysisMiddleware(PromptInjectionMiddleware):
    """长期旅程视角 Middleware。

    会话开始时检查上次分析时间，超过 3 天则触发 LLM 分析，
    将结构化摘要注入 Coach system prompt。

    fail-open：分析失败时跳过注入，Coach 正常运行。
    """

    def __init__(self) -> None:
        super().__init__()
        self._summary: str | None = None
        self._analyzed = False

    def should_inject(self) -> bool:
        return self._summary is not None

    def get_prompt(self) -> str:
        return self._summary or ""

    def _read_file(self, backend: Any, path: str) -> str | None:
        """从 backend 读取文件，返回内容或 None。"""
        try:
            result = backend.read_file(path)
            return result if result else None
        except Exception:  # noqa: BLE001
            return None

    def _write_file(self, backend: Any, path: str, content: str) -> None:
        """向 backend 写入文件。"""
        try:
            backend.write_file(path, content)
        except Exception:  # noqa: BLE001
            logger.warning("JourneyAnalysisMW: failed to write %s", path)

    def _should_trigger(self, backend: Any) -> bool:
        """检查是否超过分析间隔。"""
        raw = self._read_file(backend, _LAST_ANALYSIS_KEY)
        if not raw:
            return True

        try:
            data = json.loads(raw)
            last_ts = datetime.fromisoformat(data["timestamp"])
            elapsed = datetime.now(timezone.utc) - last_ts
            return elapsed.days >= _ANALYSIS_INTERVAL_DAYS
        except (json.JSONDecodeError, KeyError, ValueError):
            return True

    def _record_analysis_time(self, backend: Any) -> None:
        """记录本次分析时间。"""
        content = json.dumps(
            {"timestamp": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
        )
        self._write_file(backend, _LAST_ANALYSIS_KEY, content)

    def _build_analysis_prompt(
        self,
        markers_content: str,
        agents_content: str,
        pattern_index: str | None,
    ) -> str:
        """构建发送给分析 LLM 的 prompt。"""
        sections = [
            "Analyze this user's recent timeline and behavioral patterns.",
            "Produce a concise coaching brief (3-5 bullet points) for the Coach's next session.",
            "Focus on: upcoming high-risk events, repeated behavioral patterns, identity narrative shifts.",
            "",
            "## Forward Markers (upcoming events)",
            markers_content or "(empty)",
            "",
            "## Coach Memory",
            agents_content or "(empty)",
        ]
        if pattern_index:
            sections.extend(["", "## Known Patterns", pattern_index])

        sections.extend([
            "",
            "## Output Format",
            "Return ONLY a markdown section starting with `## Journey Analysis Brief`.",
            "Keep it under 300 words. Use bullet points. Be specific and actionable.",
        ])
        return "\n".join(sections)

    async def _run_analysis(self, backend: Any, model: Any) -> str | None:
        """执行 LLM 分析，返回摘要或 None。"""
        markers = self._read_file(backend, "/user/timeline/markers.json")
        agents = self._read_file(backend, "/user/coach/AGENTS.md")
        patterns = self._read_file(backend, _PATTERN_INDEX_KEY)

        if not markers and not agents:
            logger.debug("JourneyAnalysisMW: no data to analyze, skipping")
            return None

        prompt = self._build_analysis_prompt(markers, agents, patterns)

        try:
            from voliti.config.models import ModelRegistry

            analysis_model = ModelRegistry.get("summarizer")
            response = await analysis_model.ainvoke(prompt)
            summary = response.content if hasattr(response, "content") else str(response)

            if not summary or len(summary.strip()) < 10:
                logger.warning("JourneyAnalysisMW: empty or too short analysis result")
                return None

            return summary.strip()
        except Exception:  # noqa: BLE001
            logger.warning("JourneyAnalysisMW: LLM analysis failed", exc_info=True)
            return None

    async def prepare(self, backend: Any, model: Any) -> None:
        """在会话开始时调用，检查是否需要分析并执行。

        由 agent 运行时在首次 model call 前调用。
        """
        if self._analyzed:
            return

        self._analyzed = True

        if not self._should_trigger(backend):
            logger.debug("JourneyAnalysisMW: within interval, skipping analysis")
            return

        logger.info("JourneyAnalysisMW: triggering analysis")
        summary = await self._run_analysis(backend, model)

        if summary:
            self._summary = summary
            self._record_analysis_time(backend)
            logger.info("JourneyAnalysisMW: analysis complete, summary ready for injection")
