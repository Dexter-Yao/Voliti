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
_MAX_CONTENT_LENGTH = 8000

_MARKERS_KEY = "/user/timeline/markers.json"
_AGENTS_KEY = "/user/coach/AGENTS.md"
_LAST_ANALYSIS_KEY = "/user/derived/last_journey_analysis.json"
_PATTERN_INDEX_KEY = "/user/derived/pattern_index.md"


def _get_session_mode() -> str:
    try:
        from langgraph.config import get_config

        cfg = get_config()
        return cfg.get("configurable", {}).get("session_mode", "coaching")
    except Exception:  # noqa: BLE001
        return "coaching"


class JourneyAnalysisMiddleware(PromptInjectionMiddleware):
    """长期旅程视角 Middleware。

    在 wrap_model_call 中检查上次分析时间，超过 3 天则触发 LLM 分析，
    将结构化摘要注入 Coach system prompt。

    fail-open：分析失败时跳过注入，Coach 正常运行。
    Onboarding 会话跳过分析（新用户无数据可分析）。
    """

    def __init__(self) -> None:
        super().__init__()
        self._summary: str | None = None
        self._prepared = False
        self._model: Any = None

    def should_inject(self) -> bool:
        return self._summary is not None

    def get_prompt(self) -> str:
        return self._summary or ""

    def _get_backend(self) -> Any | None:
        """从 LangGraph 运行时获取 backend。"""
        try:
            from langgraph.config import get_config

            cfg = get_config()
            return cfg.get("backend")
        except Exception:  # noqa: BLE001
            return None

    def _should_trigger(self, backend: Any) -> bool:
        """检查是否超过分析间隔。首次使用或数据损坏时触发。"""
        try:
            raw = backend.read_file(_LAST_ANALYSIS_KEY)
            if not raw:
                return True
            data = json.loads(raw)
            last_ts = datetime.fromisoformat(data["timestamp"])
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
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

    def _has_meaningful_markers(self, markers_str: str | None) -> bool:
        """检查 markers 是否包含实际内容（非空列表）。"""
        if not markers_str:
            return False
        try:
            data = json.loads(markers_str)
            return bool(data.get("markers"))
        except (json.JSONDecodeError, AttributeError):
            return False

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
            markers_content[:_MAX_CONTENT_LENGTH] or "(empty)",
            "",
            "## Coach Memory",
            agents_content[:_MAX_CONTENT_LENGTH] or "(empty)",
        ]
        if pattern_index:
            sections.extend(["", "## Known Patterns", pattern_index[:_MAX_CONTENT_LENGTH]])
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

        has_markers = self._has_meaningful_markers(markers)
        if not has_markers and not agents:
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

    async def _maybe_analyze(self, backend: Any) -> None:
        """检查是否需要分析并执行。在首次 model call 时调用。"""
        if self._prepared:
            return

        self._prepared = True

        if _get_session_mode() == "onboarding":
            logger.debug("JourneyAnalysisMW: onboarding session, skipping")
            return

        if not self._should_trigger(backend):
            logger.debug("JourneyAnalysisMW: within interval, skipping analysis")
            return

        logger.info("JourneyAnalysisMW: triggering analysis")
        summary = await self._run_analysis(backend)

        if summary:
            self._summary = summary
            self._record_analysis_time(backend)
            logger.info("JourneyAnalysisMW: analysis complete, summary ready for injection")

    async def awrap_model_call(self, request, handler):
        """异步路径：在首次调用时触发分析，然后注入摘要。"""
        if not self._prepared:
            backend = self._get_backend()
            if backend:
                await self._maybe_analyze(backend)

        return await handler(self._inject(request))

    def wrap_model_call(self, request, handler):
        """同步路径：跳过分析（需要 async），仅注入已有摘要。"""
        return handler(self._inject(request))
