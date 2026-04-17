# ABOUTME: 日终 Pipeline 单元测试
# ABOUTME: 验证 thread 封存、日摘要生成、unsealed thread 查找逻辑

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from voliti.config.prompts import PromptRegistry
from voliti.pipeline.day_end import (
    _extract_messages_text,
    find_unsealed_threads,
    generate_day_summary,
    run_day_end_pipeline,
    seal_thread,
)


class TestSealThread:
    @pytest.mark.asyncio
    async def test_seal_updates_metadata(self) -> None:
        client = AsyncMock()
        client.threads.update = AsyncMock()

        result = await seal_thread(client, "thread-001")

        assert result is True
        client.threads.update.assert_called_once()
        call_kwargs = client.threads.update.call_args
        assert call_kwargs.args[0] == "thread-001"
        meta = call_kwargs.kwargs["metadata"]
        assert meta["segment_status"] == "sealed"
        assert "sealed_at" in meta

    @pytest.mark.asyncio
    async def test_seal_returns_false_on_failure(self) -> None:
        client = AsyncMock()
        client.threads.update = AsyncMock(side_effect=Exception("API error"))

        result = await seal_thread(client, "thread-001")

        assert result is False


class TestFindUnsealedThreads:
    @pytest.mark.asyncio
    async def test_finds_threads_before_date(self) -> None:
        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[
            {"thread_id": "t1", "metadata": {"user_id": "u1", "date": "2026-04-12"}},
            {"thread_id": "t2", "metadata": {"user_id": "u1", "date": "2026-04-13"}},
            {"thread_id": "t3", "metadata": {"user_id": "u1", "date": "2026-04-11", "segment_status": "sealed"}},
        ])

        result = await find_unsealed_threads(client, user_id="u1", before_date="2026-04-13")

        assert len(result) == 1
        assert result[0]["thread_id"] == "t1"

    @pytest.mark.asyncio
    async def test_returns_empty_on_failure(self) -> None:
        client = AsyncMock()
        client.threads.search = AsyncMock(side_effect=Exception("API error"))

        result = await find_unsealed_threads(client, user_id="u1", before_date="2026-04-13")

        assert result == []


class TestExtractMessagesText:
    def test_extracts_human_and_ai_messages(self) -> None:
        state = {
            "values": {
                "messages": [
                    {"type": "human", "content": "今天 72.3"},
                    {"type": "ai", "content": "记录了你的体重"},
                    {"type": "tool", "content": "write_file result"},
                ]
            }
        }

        result = _extract_messages_text(state)

        assert "用户: 今天 72.3" in result
        assert "Coach: 记录了你的体重" in result
        assert "write_file" not in result

    def test_returns_empty_for_no_messages(self) -> None:
        assert _extract_messages_text({"values": {"messages": []}}) == ""
        assert _extract_messages_text({"values": {}}) == ""
        assert _extract_messages_text({}) == ""


class TestGenerateDaySummary:
    def setup_method(self) -> None:
        PromptRegistry.reset()

    def teardown_method(self) -> None:
        PromptRegistry.reset()

    @pytest.mark.asyncio
    async def test_uses_prompt_registry_templates_for_summary_messages(
        self,
        tmp_path: Path,
    ) -> None:
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "day_summary_system.j2").write_text(
            "系统提示：为 {{ date_str }} 生成摘要。"
        )
        (prompts_dir / "day_summary_user.j2").write_text(
            "用户提示：{{ date_str }} => {{ conversation_text }}"
        )
        PromptRegistry.load(prompts_dir)

        client = AsyncMock()
        client.threads.get_state = AsyncMock(return_value={
            "values": {
                "messages": [
                    {"type": "human", "content": "今天体重 72.3kg"},
                    {"type": "ai", "content": "已记录并建议晚饭前散步 15 分钟"},
                ]
            }
        })
        client.store.put_item = AsyncMock()

        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=MagicMock(content="72.3kg，完成记录并安排散步"))

        with patch("voliti.pipeline.day_end.ModelRegistry.get", return_value=model):
            summary = await generate_day_summary(
                client,
                "thread-001",
                date_str="2026-04-12",
                namespace=("voliti", "u1"),
            )

        assert summary == "72.3kg，完成记录并安排散步"
        model.ainvoke.assert_awaited_once_with([
            SystemMessage(content="系统提示：为 2026-04-12 生成摘要。"),
            HumanMessage(
                content=(
                    "用户提示：2026-04-12 => "
                    "用户: 今天体重 72.3kg\n\nCoach: 已记录并建议晚饭前散步 15 分钟"
                )
            ),
        ])
        client.store.put_item.assert_awaited_once()


class TestRunDayEndPipelineTimezone:
    @pytest.mark.asyncio
    async def test_pipeline_uses_user_timezone(self) -> None:
        """UTC 00:30 时，Asia/Shanghai 已是次日，today 应为本地日期。"""
        # 2026-04-13 00:30 UTC == 2026-04-13 08:30 CST
        now = datetime(2026, 4, 13, 0, 30, 0, tzinfo=timezone.utc)
        expected_local_date = "2026-04-13"

        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.put_item = AsyncMock()
        client.store.get_item = AsyncMock(return_value=None)

        with patch("voliti.pipeline.day_end.compute_and_write_briefing", new_callable=AsyncMock) as mock_briefing:
            mock_briefing.return_value = "briefing text"
            result = await run_day_end_pipeline(
                client,
                user_id="u1",
                namespace=("voliti", "u1"),
                now=now,
                user_timezone="Asia/Shanghai",
            )

        assert result["today"] == expected_local_date

    @pytest.mark.asyncio
    async def test_pipeline_utc_fallback_without_timezone(self) -> None:
        """不传时区时，today 使用 UTC 日期。"""
        # 2026-04-12 23:30 UTC（CST 已是 2026-04-13，但无时区参数应取 UTC）
        now = datetime(2026, 4, 12, 23, 30, 0, tzinfo=timezone.utc)
        expected_utc_date = "2026-04-12"

        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.put_item = AsyncMock()
        client.store.get_item = AsyncMock(return_value=None)

        with patch("voliti.pipeline.day_end.compute_and_write_briefing", new_callable=AsyncMock) as mock_briefing:
            mock_briefing.return_value = "briefing text"
            result = await run_day_end_pipeline(
                client,
                user_id="u1",
                namespace=("voliti", "u1"),
                now=now,
            )

        assert result["today"] == expected_utc_date
