# ABOUTME: CoachClient 超时配置测试
# ABOUTME: 验证流式请求保留短连接超时，并使用配置的读写超时

import httpx

from voliti_eval import client as client_module
from voliti_eval.client import CoachClient, build_client_timeout


def test_build_client_timeout_uses_short_connect_timeout() -> None:
    timeout = build_client_timeout(300)

    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 5
    assert timeout.pool == 5
    assert timeout.read == 300
    assert timeout.write == 300


def test_coach_client_uses_configured_turn_timeout(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get_client(*, url: str, timeout: httpx.Timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return object()

    monkeypatch.setattr(client_module, "get_client", fake_get_client)

    CoachClient("http://localhost:2025", turn_timeout_seconds=180)

    timeout = captured["timeout"]
    assert captured["url"] == "http://localhost:2025"
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 5
    assert timeout.pool == 5
    assert timeout.read == 180
    assert timeout.write == 180
