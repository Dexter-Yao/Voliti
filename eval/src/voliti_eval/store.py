# ABOUTME: LangGraph Store 状态管理
# ABOUTME: 为评估场景预填充用户档案/LifeSign/Coach 记忆，运行后清理；支持动态 namespace 隔离

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from voliti_eval.models import PreState

logger = logging.getLogger(__name__)

STORE_NAMESPACE_PREFIX = "voliti"


def make_namespace(user_id: str = "user") -> tuple[str, str]:
    """构造 Store namespace，与 backend agent.py 中 _resolve_user_namespace 一致。"""
    return (STORE_NAMESPACE_PREFIX, user_id)


def make_file_value(content: str) -> dict[str, Any]:
    """构造与 deepagents.backends.utils.create_file_data 兼容的 Store value。

    格式：{version: "1", content: list[str], created_at: str, modified_at: str}
    """
    now = datetime.now(UTC).isoformat()
    return {
        "version": "1",
        "content": content.split("\n"),
        "created_at": now,
        "modified_at": now,
    }


def unwrap_file_value(value: dict[str, Any]) -> str:
    """解包统一文件封装值。"""
    content = value.get("content")
    if not isinstance(content, list) or not all(isinstance(line, str) for line in content):
        raise ValueError("content must be list[str]")
    return "\n".join(content)


async def populate_store(
    store_client: Any, pre_state: PreState, *, user_id: str = "user"
) -> None:
    """将 seed 的 pre_state 写入 LangGraph Store。"""
    ns = make_namespace(user_id)

    if pre_state.profile:
        await store_client.put_item(ns, key="/profile/context.md", value=make_file_value(pre_state.profile))
        logger.info("[%s] Populated /profile/context.md", user_id)

    # 生成 LifeSign 索引文件
    index_lines = ["# LifeSign Index"]
    for plan in pre_state.coping_plans:
        plan_data = plan.model_dump()
        plan_json = json.dumps(plan_data, ensure_ascii=False, indent=2)
        await store_client.put_item(ns, key=f"/coping_plans/{plan.id}.json", value=make_file_value(plan_json))
        logger.info("[%s] Populated /coping_plans/%s.json", user_id, plan.id)
        index_lines.append(
            f'- {plan.id}: "{plan.trigger.get("situation", "")}" → {plan.action} '
            f"[{plan.status}, {plan.success_count}/{plan.activated_count} success]"
        )

    if pre_state.coping_plans:
        await store_client.put_item(
            ns, key="/coping_plans_index.md", value=make_file_value("\n".join(index_lines))
        )
        logger.info("[%s] Populated /coping_plans_index.md", user_id)

    # 将 LifeSign 索引追加到 coach memory（确保 Coach 在 agent_memory 中看到预案列表）
    coach_memory_parts: list[str] = []
    if pre_state.coach_memory:
        coach_memory_parts.append(pre_state.coach_memory)
    if index_lines and len(index_lines) > 1:  # 有预案时追加索引
        coach_memory_parts.append("\n".join(index_lines))

    if coach_memory_parts:
        await store_client.put_item(
            ns, key="/coach/AGENTS.md", value=make_file_value("\n\n".join(coach_memory_parts))
        )
        logger.info("[%s] Populated /coach/AGENTS.md (with LifeSign index)", user_id)

    # DashboardConfig
    if pre_state.dashboard_config:
        dc_data = pre_state.dashboard_config.model_dump(exclude_none=True)
        dc_json = json.dumps(dc_data, ensure_ascii=False, indent=2)
        await store_client.put_item(ns, key="/profile/dashboardConfig", value=make_file_value(dc_json))
        logger.info("[%s] Populated /profile/dashboardConfig", user_id)

    # Chapter
    if pre_state.chapter:
        ch_data = pre_state.chapter.model_dump()
        ch_json = json.dumps(ch_data, ensure_ascii=False, indent=2)
        await store_client.put_item(ns, key="/chapter/current.json", value=make_file_value(ch_json))
        logger.info("[%s] Populated /chapter/current.json", user_id)

    # Forward Markers
    if pre_state.forward_markers:
        markers_data = {
            "markers": [m.model_dump(exclude_none=True) for m in pre_state.forward_markers]
        }
        markers_json = json.dumps(markers_data, ensure_ascii=False, indent=2)
        await store_client.put_item(ns, key="/timeline/markers.json", value=make_file_value(markers_json))
        logger.info("[%s] Populated /timeline/markers.json (%d markers)", user_id, len(pre_state.forward_markers))

    for entry in pre_state.ledger_entries:
        entry_data = json.dumps(entry.data, ensure_ascii=False, indent=2)
        key = f"/ledger/{entry.date}/{entry.time}_{entry.type}.json"
        await store_client.put_item(ns, key=key, value=make_file_value(entry_data))
        logger.info("[%s] Populated %s", user_id, key)


async def clear_store(store_client: Any, *, user_id: str = "user") -> None:
    """清空指定 namespace 下的所有 Store 项。"""
    ns = make_namespace(user_id)
    limit = 100
    deleted = 0

    while True:
        result = await store_client.search_items(ns, limit=limit, offset=0)
        item_list: list = result.get("items", []) if isinstance(result, dict) else result

        if not item_list:
            break

        for item in item_list:
            key = item.get("key") if isinstance(item, dict) else getattr(item, "key", None)
            if key:
                await store_client.delete_item(ns, key=key)
                deleted += 1

        if len(item_list) < limit:
            break

    if deleted:
        logger.info("[%s] Cleared %d items from Store", user_id, deleted)
