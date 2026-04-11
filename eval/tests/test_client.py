# ABOUTME: CoachClient 超时配置测试
# ABOUTME: 验证流式请求保留短连接超时，并使用配置的读写超时

import httpx

from voliti_eval import client as client_module
from voliti_eval.client import CoachClient, build_client_timeout, decorate_interrupt_payload


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

    CoachClient("http://localhost:2025", assistant_id="coach", turn_timeout_seconds=180)

    timeout = captured["timeout"]
    assert captured["url"] == "http://localhost:2025"
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 5
    assert timeout.pool == 5
    assert timeout.read == 180
    assert timeout.write == 180


def test_decorate_interrupt_payload_adds_interrupt_id() -> None:
    payload = {
        "type": "a2ui",
        "components": [],
        "layout": "three-quarter",
        "metadata": {"card_id": "card_123"},
    }
    interrupt = {
        "id": "interrupt_123",
        "value": payload,
    }

    decorated = decorate_interrupt_payload(payload, interrupt)

    assert decorated["metadata"]["card_id"] == "card_123"
    assert decorated["metadata"]["interrupt_id"] == "interrupt_123"


def test_coach_client_builds_session_type_config_and_thread_metadata(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeThreads:
        async def create(self, metadata: dict[str, str]):
            captured["metadata"] = metadata
            return {"thread_id": "thread_123"}

    class FakeClient:
        def __init__(self) -> None:
            self.threads = FakeThreads()

    monkeypatch.setattr(client_module, "get_client", lambda **_: FakeClient())

    client = CoachClient("http://localhost:2025", assistant_id="coach", turn_timeout_seconds=180)
    client.with_user_id("user_123").with_session_type("onboarding")

    config = client._build_config()
    assert config == {
        "configurable": {
            "user_id": "user_123",
            "session_type": "onboarding",
        }
    }

    import asyncio

    thread_id = asyncio.run(client.create_thread())
    assert thread_id == "thread_123"
    assert captured["metadata"] == {
        "user_id": "user_123",
        "session_type": "onboarding",
    }
