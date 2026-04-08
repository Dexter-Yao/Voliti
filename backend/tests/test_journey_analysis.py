# ABOUTME: JourneyAnalysisMiddleware 单元测试
# ABOUTME: 覆盖 should_trigger、analyze、fail-open 和 prompt 注入逻辑

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voliti.middleware.journey_analysis import (
    JourneyAnalysisMiddleware,
    _ANALYSIS_INTERVAL_DAYS,
    _LAST_ANALYSIS_KEY,
)


class TestShouldTrigger:

    def test_triggers_when_no_previous_analysis(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        backend.read_file.return_value = None
        assert mw._should_trigger(backend) is True

    def test_triggers_when_interval_exceeded(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        old_ts = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        backend.read_file.return_value = json.dumps({"timestamp": old_ts})
        assert mw._should_trigger(backend) is True

    def test_skips_when_within_interval(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        recent_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        backend.read_file.return_value = json.dumps({"timestamp": recent_ts})
        assert mw._should_trigger(backend) is False

    def test_triggers_on_corrupted_timestamp(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        backend.read_file.return_value = "not valid json"
        assert mw._should_trigger(backend) is True

    def test_triggers_on_missing_key(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        backend.read_file.return_value = json.dumps({"other": "data"})
        assert mw._should_trigger(backend) is True

    def test_handles_naive_datetime(self) -> None:
        """naive datetime（无时区）应被正确处理而非抛异常。"""
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        naive_ts = datetime.now().isoformat()  # no timezone
        backend.read_file.return_value = json.dumps({"timestamp": naive_ts})
        # 不应抛异常，应正常返回 bool
        result = mw._should_trigger(backend)
        assert isinstance(result, bool)


class TestHasMeaningfulMarkers:

    def test_empty_string(self) -> None:
        mw = JourneyAnalysisMiddleware()
        assert mw._has_meaningful_markers("") is False
        assert mw._has_meaningful_markers(None) is False

    def test_empty_markers_list(self) -> None:
        mw = JourneyAnalysisMiddleware()
        assert mw._has_meaningful_markers('{"markers": []}') is False

    def test_nonempty_markers_list(self) -> None:
        mw = JourneyAnalysisMiddleware()
        data = json.dumps({"markers": [{"id": "mk_001"}]})
        assert mw._has_meaningful_markers(data) is True

    def test_invalid_json(self) -> None:
        mw = JourneyAnalysisMiddleware()
        assert mw._has_meaningful_markers("not json") is False


class TestAnalyze:

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        backend.read_file.return_value = None
        result = await mw._run_analysis(backend)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_summary_on_success(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()

        markers = json.dumps({"markers": [{"id": "mk_001", "description": "聚餐"}]})
        agents = "# Coach Memory\nUser prefers morning check-ins."

        def read_side_effect(path: str) -> str | None:
            if "markers" in path:
                return markers
            if "AGENTS" in path:
                return agents
            return None

        backend.read_file.side_effect = read_side_effect

        mock_response = MagicMock()
        mock_response.content = "## Journey Analysis Brief\n- 用户即将有聚餐活动"

        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch("voliti.config.models.ModelRegistry") as mock_registry:
            mock_registry.get.return_value = mock_model
            result = await mw._run_analysis(backend)

        assert result is not None
        assert "Journey Analysis Brief" in result

    @pytest.mark.asyncio
    async def test_returns_none_on_llm_failure(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        markers = json.dumps({"markers": [{"id": "mk_001"}]})
        backend.read_file.return_value = markers

        with patch("voliti.config.models.ModelRegistry") as mock_registry:
            mock_registry.get.side_effect = RuntimeError("LLM unavailable")
            result = await mw._run_analysis(backend)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        markers = json.dumps({"markers": [{"id": "mk_001"}]})
        backend.read_file.return_value = markers

        mock_response = MagicMock()
        mock_response.content = ""

        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch("voliti.config.models.ModelRegistry") as mock_registry:
            mock_registry.get.return_value = mock_model
            result = await mw._run_analysis(backend)

        assert result is None

    @pytest.mark.asyncio
    async def test_skips_on_empty_markers_list(self) -> None:
        """markers.json 存在但列表为空时应跳过分析。"""
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()

        def read_side_effect(path: str) -> str | None:
            if "markers" in path:
                return '{"markers": []}'
            return None

        backend.read_file.side_effect = read_side_effect
        result = await mw._run_analysis(backend)
        assert result is None


class TestPromptInjection:

    def test_no_injection_without_summary(self) -> None:
        mw = JourneyAnalysisMiddleware()
        assert mw.should_inject() is False
        assert mw.get_prompt() == ""

    def test_injection_with_summary(self) -> None:
        mw = JourneyAnalysisMiddleware()
        mw._summary = "## Journey Analysis Brief\n- Test finding"
        assert mw.should_inject() is True
        assert "Journey Analysis Brief" in mw.get_prompt()


class TestMaybeAnalyze:

    @pytest.mark.asyncio
    async def test_skips_when_within_interval(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        recent_ts = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        backend.read_file.return_value = json.dumps({"timestamp": recent_ts})

        await mw._maybe_analyze(backend)
        assert mw._summary is None
        assert mw._prepared is True

    @pytest.mark.asyncio
    async def test_only_runs_once(self) -> None:
        mw = JourneyAnalysisMiddleware()
        mw._prepared = True
        backend = MagicMock()

        await mw._maybe_analyze(backend)
        backend.read_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_during_onboarding(self) -> None:
        """onboarding 会话应跳过分析。"""
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()

        with patch("voliti.middleware.journey_analysis.get_session_mode", return_value="onboarding"):
            await mw._maybe_analyze(backend)

        assert mw._prepared is True
        assert mw._summary is None
        backend.read_file.assert_not_called()
