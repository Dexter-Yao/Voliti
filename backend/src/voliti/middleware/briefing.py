# ABOUTME: BriefingMiddleware — 会话开始时注入预计算的 Coach Briefing
# ABOUTME: 从 Store 读取 /user/derived/briefing.md，fail-open 设计，onboarding 跳过

from __future__ import annotations

import logging
from typing import Any

from deepagents.backends.protocol import BACKEND_TYPES, BackendProtocol
from langchain.tools import ToolRuntime

from voliti.middleware.base import PromptInjectionMiddleware, get_session_type
from voliti.store_contract import BRIEFING_DERIVED_KEY

logger = logging.getLogger(__name__)


class BriefingMiddleware(PromptInjectionMiddleware):
    """预计算 Briefing 注入 Middleware。

    在 wrap_model_call 中从 Store 读取由 briefing 脚本预生成的
    /user/derived/briefing.md，注入到 Coach system prompt。

    fail-open：读取失败时跳过注入，Coach 正常运行。
    Onboarding 会话跳过（新用户无历史数据）。
    """

    def __init__(self, *, backend: BACKEND_TYPES | None = None) -> None:
        super().__init__()
        self._backend = backend
        self._briefing: str | None = None
        self._loaded = False

    def should_inject(self) -> bool:
        return self._briefing is not None

    def get_prompt(self) -> str:
        return self._briefing or ""

    def _resolve_backend(self, *, state: Any, runtime: Any) -> BackendProtocol | None:
        """基于当前 runtime 解析 backend。"""
        try:
            from langgraph.config import get_config

            config = get_config()
        except Exception:  # noqa: BLE001
            return None

        if self._backend is None:
            return None

        if callable(self._backend):
            tool_runtime = ToolRuntime(
                state=state,
                context=runtime.context,
                config=config,
                stream_writer=runtime.stream_writer,
                tool_call_id=None,
                store=runtime.store,
            )
            return self._backend(tool_runtime)  # type: ignore[call-arg]
        return self._backend

    def _load_briefing(self, backend: BackendProtocol) -> str | None:
        """从 Store 读取预计算的 briefing 文件。"""
        try:
            content = backend.read_file(BRIEFING_DERIVED_KEY)
            if content and content.strip():
                return content.strip()
        except Exception:  # noqa: BLE001
            logger.debug("BriefingMW: failed to read briefing, skipping")
        return None

    def _maybe_load(self, *, state: Any, runtime: Any) -> None:
        """首次 model call 时加载 briefing（仅一次）。"""
        if self._loaded:
            return
        self._loaded = True

        if get_session_type() == "onboarding":
            return

        backend = self._resolve_backend(state=state, runtime=runtime)
        if backend is None:
            return

        self._briefing = self._load_briefing(backend)
        if self._briefing:
            logger.debug("BriefingMW: briefing loaded (%d chars)", len(self._briefing))

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        self._maybe_load(state=request.state, runtime=request.runtime)
        return super().wrap_model_call(request, handler)

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        self._maybe_load(state=request.state, runtime=request.runtime)
        return await super().awrap_model_call(request, handler)
