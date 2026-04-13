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

    从 Store 读取由 briefing 脚本预生成的 briefing 文件，注入到 Coach system prompt。
    遵循 DeepAgent MemoryMiddleware 的 download_files/adownload_files 模式。

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
        """基于当前 runtime 解析 backend，复用 DeepAgent MemoryMiddleware 的模式。"""
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

    def _download_briefing(self, backend: BackendProtocol) -> str | None:
        """同步读取 briefing（用于 wrap_model_call）。"""
        try:
            results = backend.download_files([BRIEFING_DERIVED_KEY])
            if results and results[0].error is None and results[0].content is not None:
                text = results[0].content.decode("utf-8").strip()
                return text if text else None
        except Exception:  # noqa: BLE001
            logger.debug("BriefingMW: failed to download briefing, skipping")
        return None

    async def _adownload_briefing(self, backend: BackendProtocol) -> str | None:
        """异步读取 briefing（用于 awrap_model_call）。"""
        try:
            results = await backend.adownload_files([BRIEFING_DERIVED_KEY])
            if results and results[0].error is None and results[0].content is not None:
                text = results[0].content.decode("utf-8").strip()
                return text if text else None
        except Exception:  # noqa: BLE001
            logger.debug("BriefingMW: failed to download briefing, skipping")
        return None

    def _maybe_load_sync(self, *, state: Any, runtime: Any) -> None:
        """同步加载 briefing（仅一次）。"""
        if self._loaded:
            return
        self._loaded = True

        if get_session_type() == "onboarding":
            return

        backend = self._resolve_backend(state=state, runtime=runtime)
        if backend is None:
            return

        self._briefing = self._download_briefing(backend)
        if self._briefing:
            logger.debug("BriefingMW: briefing loaded (%d chars)", len(self._briefing))

    async def _maybe_load_async(self, *, state: Any, runtime: Any) -> None:
        """异步加载 briefing（仅一次）。"""
        if self._loaded:
            return
        self._loaded = True

        if get_session_type() == "onboarding":
            return

        backend = self._resolve_backend(state=state, runtime=runtime)
        if backend is None:
            return

        self._briefing = await self._adownload_briefing(backend)
        if self._briefing:
            logger.debug("BriefingMW: briefing loaded (%d chars)", len(self._briefing))

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        self._maybe_load_sync(state=request.state, runtime=request.runtime)
        return super().wrap_model_call(request, handler)

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        await self._maybe_load_async(state=request.state, runtime=request.runtime)
        return await super().awrap_model_call(request, handler)
