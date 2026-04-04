# ABOUTME: LangGraph Store 状态管理
# ABOUTME: 为评估场景预填充用户档案/LifeSign/Coach 记忆，运行后清理

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from voliti_eval.models import PreState

logger = logging.getLogger(__name__)

# 与 backend agent.py 中 StoreBackend namespace 一致
STORE_NAMESPACE = ("voliti", "user")


def _make_file_value(content: str) -> dict[str, Any]:
    """构造与 deepagents.backends.utils.create_file_data 兼容的 Store value。

    格式：{content: list[str], created_at: str, modified_at: str}
    """
    now = datetime.now(UTC).isoformat()
    return {
        "content": content.split("\n"),
        "created_at": now,
        "modified_at": now,
    }


async def populate_store(store_client: Any, pre_state: PreState) -> None:
    """将 seed 的 pre_state 写入 LangGraph Store。

    Args:
        store_client: LangGraphClient.store 实例。
        pre_state: 要预填充的状态。
    """
    if pre_state.profile:
        await store_client.put_item(
            STORE_NAMESPACE,
            key="profile/context.md",
            value=_make_file_value(pre_state.profile),
        )
        logger.info("Populated profile/context.md")

    for plan in pre_state.coping_plans:
        plan_data = plan.model_dump()
        plan_json = json.dumps(plan_data, ensure_ascii=False, indent=2)
        await store_client.put_item(
            STORE_NAMESPACE,
            key=f"coping_plans/{plan.id}.json",
            value=_make_file_value(plan_json),
        )
        logger.info("Populated coping_plans/%s.json", plan.id)

    if pre_state.coach_memory:
        await store_client.put_item(
            STORE_NAMESPACE,
            key="coach/AGENTS.md",
            value=_make_file_value(pre_state.coach_memory),
        )
        logger.info("Populated coach/AGENTS.md")


async def clear_store(store_client: Any) -> None:
    """清空 Store 中 STORE_NAMESPACE 下的所有项。

    通过 search_items 列出所有 key，逐一删除。
    """
    offset = 0
    limit = 100
    deleted = 0

    while True:
        result = await store_client.search_items(
            STORE_NAMESPACE, limit=limit, offset=offset
        )
        # search_items 返回 {"items": [...]} dict
        item_list: list = result.get("items", []) if isinstance(result, dict) else result

        if not item_list:
            break

        for item in item_list:
            key = item.get("key") if isinstance(item, dict) else getattr(item, "key", None)
            if key:
                await store_client.delete_item(STORE_NAMESPACE, key=key)
                deleted += 1

        if len(item_list) < limit:
            break
        offset += limit

    if deleted:
        logger.info("Cleared %d items from Store namespace %s", deleted, STORE_NAMESPACE)
