# ABOUTME: BriefingMiddleware 单元测试
# ABOUTME: 验证 briefing 注入、fail-open、onboarding 跳过行为

from __future__ import annotations

from unittest.mock import MagicMock, patch

from voliti.middleware.briefing import BriefingMiddleware


def _make_download_response(content: str | None = None, error: str | None = None) -> MagicMock:
    """构造 FileDownloadResponse mock。"""
    resp = MagicMock()
    resp.error = error
    resp.content = content.encode("utf-8") if content else None
    return resp


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
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_loads_briefing_for_coaching_session(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.download_files.return_value = [
            _make_download_response("## Coach Briefing\n距上次会话：1 天"),
        ]

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is not None
        assert "Coach Briefing" in mw._briefing

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_backend_is_none(self, mock_session: MagicMock) -> None:
        mw = BriefingMiddleware(backend=None)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_download_fails(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.download_files.side_effect = Exception("store unavailable")

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is None
        assert mw._loaded is True

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_loads_only_once(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.download_files.return_value = [
            _make_download_response("briefing content"),
        ]

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        mock_backend.download_files.assert_called_once()

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_file_not_found(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.download_files.return_value = [
            _make_download_response(error="file_not_found"),
        ]

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is None

    @patch("voliti.middleware.briefing.get_session_type", return_value="coaching")
    def test_fail_open_when_empty_content(self, mock_session: MagicMock) -> None:
        mock_backend = MagicMock()
        mock_backend.download_files.return_value = [
            _make_download_response("   "),
        ]

        mw = BriefingMiddleware(backend=mock_backend)
        mw._resolve_backend = MagicMock(return_value=mock_backend)
        mw._maybe_load_sync(state={}, runtime=MagicMock())
        assert mw._briefing is None
