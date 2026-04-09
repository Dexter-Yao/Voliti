# ABOUTME: Eval Store 契约测试
# ABOUTME: 验证文件封装值、分页删除与 namespace 隔离符合运行时契约

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from voliti_eval.store import clear_store, make_namespace, make_file_value, unwrap_file_value

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "contracts" / "fixtures" / "store"


class FakeStoreClient:
    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.items = items
        self.deleted: list[tuple[tuple[str, str], str]] = []
        self.search_calls: list[tuple[tuple[str, str], int, int]] = []

    async def search_items(self, namespace: tuple[str, str], limit: int, offset: int) -> dict[str, Any]:
        self.search_calls.append((namespace, limit, offset))
        return {"items": self.items[offset:offset + limit]}

    async def delete_item(self, namespace: tuple[str, str], key: str) -> None:
        self.deleted.append((namespace, key))
        self.items = [item for item in self.items if item.get("key") != key]


def test_make_namespace_uses_user_id() -> None:
    assert make_namespace("eval_0001") == ("voliti", "eval_0001")


def test_make_file_value_wraps_content_lines() -> None:
    value = make_file_value('{"hello":"world"}')
    assert value["version"] == "1"
    assert unwrap_file_value(value) == '{"hello":"world"}'


def test_shared_chapter_fixture_round_trip() -> None:
    fixture = FIXTURES_DIR / "chapter_current.value.json"
    value = json.loads(fixture.read_text(encoding="utf-8"))
    parsed = json.loads(unwrap_file_value(value))
    assert parsed["fixture_type"] == "chapter_current"


@pytest.mark.asyncio
async def test_clear_store_paginates_without_skipping_items() -> None:
    client = FakeStoreClient([{"key": f"/item-{index}"} for index in range(150)])

    await clear_store(client, user_id="eval_0001")

    assert client.search_calls == [
        (("voliti", "eval_0001"), 100, 0),
        (("voliti", "eval_0001"), 100, 0),
    ]
    assert len(client.deleted) == 150
    assert client.deleted[0] == (("voliti", "eval_0001"), "/item-0")
    assert client.deleted[-1] == (("voliti", "eval_0001"), "/item-149")
