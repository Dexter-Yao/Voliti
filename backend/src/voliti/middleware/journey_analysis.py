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

_MARKERS_KEY = "/user/timeline/markers.json"
_AGENTS_KEY = "/user/coach/AGENTS.md"
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
        # _analyzed 必须在 _summary 赋值前设为 True，确保分析失败时不会重复触发
        self._analyzed = False
        self._model: Any = None

    def should_inject(self) -> bool:
        return self._summary is not None

    def get_prompt(self) -> str:
        return self._summary or ""

    def _should_trigger(self, backend: Any) -> bool:
        """检查是否超过分析间隔。首次使用或数据损坏时触发。"""
        try:
            raw = backend.read_file(_LAST_ANALYSIS_KEY)
            if not raw:
                return True
            data = json.loads(raw)
            last_ts = datetime.fromisoformat(data["timestamp"])
            elapsed = datetime.now(timezone.utc) - last_ts
            return elapsed.days >= _ANALYSIS_INTERVAL_DAYS
        except Exception:  # noqa: BLE001
            return True

    def _record_analysis_time(self, backend: Any) -> None:
        content = json.dumps(
            {"timestamp": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
        )
        try:
            backend.write_file(_LAST_ANALYSIS_KEY, content)
        except Exception:  # noqa: BLE001
            logger.warning("JourneyAnalysisMW: failed to write analysis timestamp")

    def _build_analysis_prompt(
        self,
        markers_content: str,
        agents_content: str,
        pattern_index: str | None,
    ) -> str:
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

    async def _run_analysis(self, backend: Any) -> str | None:
        """执行 LLM 分析，返回摘要或 None。fail-open。"""
        try:
            markers = backend.read_file(_MARKERS_KEY)
            agents = backend.read_file(_AGENTS_KEY)
            patterns = backend.read_file(_PATTERN_INDEX_KEY)
        except Exception:  # noqa: BLE001
            markers = agents = patterns = None

        if not markers and not agents:
            logger.debug("JourneyAnalysisMW: no data to analyze, skipping")
            return None

        prompt = self._build_analysis_prompt(
            markers or "", agents or "", patterns
        )

        try:
            if self._model is None:
                from voliti.config.models import ModelRegistry

                self._model = ModelRegistry.get("summarizer")

            response = await self._model.ainvoke(prompt)
            summary = response.content

            if not summary or len(summary.strip()) < 10:
                logger.warning("JourneyAnalysisMW: empty or too short analysis result")
                return None

            return summary.strip()
        except Exception:  # noqa: BLE001
            logger.warning("JourneyAnalysisMW: LLM analysis failed", exc_info=True)
            return None

    async def prepare(self, backend: Any) -> None:
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
        summary = await self._run_analysis(backend)

        if summary:
            self._summary = summary
            self._record_analysis_time(backend)
            logger.info("JourneyAnalysisMW: analysis complete, summary ready for injection")
