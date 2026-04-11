# ABOUTME: JourneyAnalysisMiddleware — 长期旅程视角分析，定期扫描用户时间轴并注入摘要
# ABOUTME: 会话触发 + 3 天时间门槛，fail-open 设计，分析失败不阻塞 Coach

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from voliti.middleware.base import PromptInjectionMiddleware, get_session_type

logger = logging.getLogger(__name__)

_ANALYSIS_INTERVAL_DAYS = 3
_MAX_CONTENT_LENGTH = 8000
_MAX_FILES_PER_DAY = 50

_MARKERS_KEY = "/user/timeline/markers.json"
_AGENTS_KEY = "/user/coach/AGENTS.md"
_LAST_ANALYSIS_KEY = "/user/derived/last_journey_analysis.json"
_PATTERN_INDEX_KEY = "/user/derived/pattern_index.md"
_SIGNAL_KIND = "candidate_signal"
_SIGNAL_SOURCE = "journey_analysis"


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

    def get_candidate_signal(self) -> dict[str, str] | None:
        """返回当前分析摘要的候选信号视图。"""
        if self._summary is None:
            return None
        return {
            "kind": _SIGNAL_KIND,
            "source": _SIGNAL_SOURCE,
            "content": self._summary,
        }

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

    def _scan_ledger_for_achievements(self, backend: Any) -> str | None:
        """扫描近 30 天 ledger 数据，检测隐性成就信号。

        两类信号：
        - 连续 ≥7 天 check-in（任何 observation/state 事件算一天）
        - 单个 LifeSign 累计 ≥3 次成功（refs.lifesign_id 匹配 + 无负面 metrics）
        Returns: 结构化的成就信号描述，或 None。
        """
        try:
            ledger_entries: list[dict] = []
            now = datetime.now(timezone.utc)
            for days_ago in range(30):
                date = now - timedelta(days=days_ago)
                date_dir = f"/user/ledger/{date.strftime('%Y-%m-%d')}"
                try:
                    listing = backend.list_files(date_dir)
                except Exception:  # noqa: BLE001
                    continue
                for fname in listing[:_MAX_FILES_PER_DAY]:
                    try:
                        content = backend.read_file(f"{date_dir}/{fname}")
                        if content:
                            entry = json.loads(content)
                            entry["_date"] = date.strftime("%Y-%m-%d")
                            ledger_entries.append(entry)
                    except Exception:  # noqa: BLE001
                        continue

            if not ledger_entries:
                return None

            signals = []

            checkin_dates = sorted({
                e["_date"]
                for e in ledger_entries
                if e.get("kind") in ("observation", "state")
            })
            if len(checkin_dates) >= 7:
                streak = 1
                max_streak = 1
                for i in range(1, len(checkin_dates)):
                    prev = datetime.strptime(checkin_dates[i - 1], "%Y-%m-%d")
                    curr = datetime.strptime(checkin_dates[i], "%Y-%m-%d")
                    if (curr - prev).days == 1:
                        streak += 1
                        max_streak = max(max_streak, streak)
                    else:
                        streak = 1
                max_streak = max(max_streak, streak)
                if max_streak >= 7:
                    signals.append(
                        f"IMPLICIT ACHIEVEMENT: User has checked in for {max_streak} consecutive days."
                    )

            lifesign_events = [
                e for e in ledger_entries
                if e.get("kind") == "observation"
                and e.get("refs", {}).get("lifesign_id")
            ]
            lifesign_successes: dict[str, int] = {}
            for e in lifesign_events:
                ls_id = e["refs"]["lifesign_id"]
                # metrics 是 array of {"key": ..., "value": ..., "quality": ...}
                # 只有明确标记 success=true 才计入，避免假阳性
                metrics = e.get("metrics", [])
                has_explicit_success = any(
                    m.get("key") == "success" and m.get("value")
                    for m in metrics
                    if isinstance(m, dict)
                )
                if has_explicit_success:
                    lifesign_successes[ls_id] = lifesign_successes.get(ls_id, 0) + 1
            for ls_id, count in lifesign_successes.items():
                if count >= 3:
                    signals.append(
                        f"IMPLICIT ACHIEVEMENT: LifeSign {ls_id} has {count} successes in the past 30 days."
                    )

            if not signals:
                return None

            return "\n".join(signals)

        except Exception:  # noqa: BLE001
            logger.debug("JourneyAnalysisMW: ledger achievement scan failed", exc_info=True)
            return None

    def _build_analysis_prompt(
        self,
        markers_content: str,
        agents_content: str,
        pattern_index: str | None,
        implicit_achievements: str | None = None,
    ) -> str:
        sections = [
            "Analyze this user's recent timeline and behavioral patterns.",
            "Produce a concise coaching brief (3-5 bullet points) for the Coach's next session.",
            "Focus on: upcoming high-risk events, repeated behavioral patterns, identity narrative shifts, and implicit achievements worth witnessing.",
            "",
            "## Forward Markers (upcoming events)",
            markers_content[:_MAX_CONTENT_LENGTH] or "(empty)",
            "",
            "## Coach Memory",
            agents_content[:_MAX_CONTENT_LENGTH] or "(empty)",
        ]
        if pattern_index:
            sections.extend(["", "## Known Patterns", pattern_index[:_MAX_CONTENT_LENGTH]])
        if implicit_achievements:
            sections.extend([
                "",
                "## Implicit Achievements Detected",
                "The following achievements were detected from ledger data. The user may not be aware of these. Consider whether they warrant a Witness Card.",
                implicit_achievements,
            ])
        sections.extend([
            "",
            "## Output Format",
            "Return ONLY a markdown section starting with `## Journey Analysis Brief`.",
            "Keep it under 300 words. Use bullet points. Be specific and actionable.",
            "If implicit achievements are detected, include a bullet recommending whether Coach should generate a Witness Card for them.",
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

        implicit_achievements = self._scan_ledger_for_achievements(backend)

        has_markers = self._has_meaningful_markers(markers)
        if not has_markers and not agents and not implicit_achievements:
            logger.debug("JourneyAnalysisMW: no data to analyze, skipping")
            return None

        prompt = self._build_analysis_prompt(
            markers or "", agents or "", patterns, implicit_achievements
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

        if get_session_type() == "onboarding":
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
