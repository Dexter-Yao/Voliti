# ABOUTME: BriefingMiddleware 单元测试
# ABOUTME: 验证 briefing 注入、fail-open、onboarding 跳过行为

from __future__ import annotations

from unittest.mock import MagicMock, patch

from voliti.middleware.briefing import BriefingMiddleware


class TestBriefingMiddleware:
    """BriefingMiddleware 行为测试。"""

    def test_should_not_inject_when_no_briefing_loaded(self) -> None:
        mw = BriefingMiddleware()
        assert mw.should_inject() is False
        assert mw.get_prompt() == ""

    def test_should_inject_when_briefing_loaded(self) -> None:
        mw = BriefingMiddleware()
        mw._briefing = "## Coach Briefing\n距上次会话：2 天"
        assert mw.should_inject() is True
        assert "Coach Briefing" in mw.get_prompt()

    @patch("voliti.middleware.briefing.get_session_type", return_value="onboarding")
    def test_skips_loading_during_onboarding(self, mock_session: MagicMock) -> None:
        mw = BriefingMiddleware(backend=MagicMock())
        mw._maybe_load(state={}, runtime=MagicMock())
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_loads_briefing_for_coaching_session(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.read_file.return_value = "## Coach Briefing\n距上次会话：1 天"

        mw = BriefingMiddleware(backend=mock_backend)
        # Directly set resolved backend to bypass get_config() in tests
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load(state={}, runtime=MagicMock(context=None, stream_writer=None, store=None))
        assert mw._briefing is not None
        assert "Coach Briefing" in mw._briefing

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_backend_is_none(self, mock_session: MagicMock) -> None:
        mw = BriefingMiddleware(backend=None)
        mw._maybe_load(state={}, runtime=MagicMock())
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_read_fails(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.read_file.side_effect = Exception("store unavailable")

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load(state={}, runtime=MagicMock(context=None, stream_writer=None, store=None))
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_loads_only_once(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.read_file.return_value = "briefing content"

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        runtime = MagicMock(context=None, stream_writer=None, store=None)
        mw._maybe_load(state={}, runtime=runtime)
        mw._maybe_load(state={}, runtime=runtime)
        mock_backend.read_file.assert_called_once()

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_empty_content(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.read_file.return_value = "   "

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load(state={}, runtime=MagicMock(context=None, stream_writer=None, store=None))
        assert mw._briefing is None
