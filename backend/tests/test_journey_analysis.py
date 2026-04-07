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
        backend.read_file.return_value = json.dumps({"markers": []})

        with patch("voliti.config.models.ModelRegistry") as mock_registry:
            mock_registry.get.side_effect = RuntimeError("LLM unavailable")
            result = await mw._run_analysis(backend)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        backend.read_file.return_value = json.dumps({"markers": []})

        mock_response = MagicMock()
        mock_response.content = ""

        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch("voliti.config.models.ModelRegistry") as mock_registry:
            mock_registry.get.return_value = mock_model
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


class TestPrepare:

    @pytest.mark.asyncio
    async def test_skips_when_within_interval(self) -> None:
        mw = JourneyAnalysisMiddleware()
        backend = MagicMock()
        recent_ts = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        backend.read_file.return_value = json.dumps({"timestamp": recent_ts})

        await mw.prepare(backend)
        assert mw._summary is None
        assert mw._analyzed is True

    @pytest.mark.asyncio
    async def test_only_runs_once(self) -> None:
        mw = JourneyAnalysisMiddleware()
        mw._analyzed = True
        backend = MagicMock()

        await mw.prepare(backend)
        backend.read_file.assert_not_called()
