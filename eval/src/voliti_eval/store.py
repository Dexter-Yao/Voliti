# ABOUTME: LangGraph Store 状态管理
# ABOUTME: 负责预填充、快照与清理 eval 运行的用户命名空间

from __future__ import annotations

import json
import logging
from typing import Any

from voliti_eval.backend_contracts import get_store_contract_module
from voliti_eval.models import PreState, StoreFileArtifact, StoreSnapshot

logger = logging.getLogger(__name__)

_STORE_CONTRACT = get_store_contract_module()

STORE_NAMESPACE_PREFIX = _STORE_CONTRACT.STORE_NAMESPACE_PREFIX


def make_namespace(user_id: str = "user") -> tuple[str, str]:
    """构造与 backend 一致的用户级 namespace。"""
    return _STORE_CONTRACT.make_user_namespace(user_id)


def make_file_value(content: str) -> dict[str, Any]:
    """构造统一文件封装值。"""
    return _STORE_CONTRACT.make_file_value(content)


def unwrap_file_value(value: dict[str, Any]) -> str:
    """解包统一文件封装值。"""
    return _STORE_CONTRACT.unwrap_file_value(value)


async def populate_store(
    store_client: Any,
    pre_state: PreState,
    *,
    user_id: str = "user",
) -> None:
    """将 seed 的 pre_state 写入 LangGraph Store。"""
    ns = make_namespace(user_id)

    if pre_state.profile:
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.PROFILE_CONTEXT_KEY,
            value=make_file_value(pre_state.profile),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.PROFILE_CONTEXT_KEY)

    if pre_state.coach_memory:
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.COACH_MEMORY_KEY,
            value=make_file_value(pre_state.coach_memory),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.COACH_MEMORY_KEY)

    if pre_state.briefing:
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.BRIEFING_STORE_KEY,
            value=make_file_value(pre_state.briefing),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.BRIEFING_STORE_KEY)

    for date, summary in pre_state.day_summaries.items():
        key = f"{_STORE_CONTRACT.DAY_SUMMARY_PREFIX}{date}.md"
        await store_client.put_item(ns, key=key, value=make_file_value(summary))
        logger.info("[%s] Populated %s", user_id, key)

    for date, archive in pre_state.conversation_archives.items():
        key = f"{_STORE_CONTRACT.CONVERSATION_ARCHIVE_PREFIX}{date}.md"
        await store_client.put_item(ns, key=key, value=make_file_value(archive))
        logger.info("[%s] Populated %s", user_id, key)

    index_lines = ["# LifeSign Index"]
    for plan in pre_state.coping_plans:
        plan_json = json.dumps(plan.model_dump(), ensure_ascii=False, indent=2)
        key = f"/coping_plans/{plan.id}.json"
        await store_client.put_item(ns, key=key, value=make_file_value(plan_json))
        logger.info("[%s] Populated %s", user_id, key)
        index_lines.append(
            f'- {plan.id}: "{plan.trigger.get("situation", "")}" → {plan.action} [{plan.status}]'
        )

    if pre_state.coping_plans:
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.COPING_PLANS_INDEX_KEY,
            value=make_file_value("\n".join(index_lines)),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.COPING_PLANS_INDEX_KEY)

    if pre_state.dashboard_config:
        dashboard_json = json.dumps(
            pre_state.dashboard_config.model_dump(exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.PROFILE_DASHBOARD_CONFIG_KEY,
            value=make_file_value(dashboard_json),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.PROFILE_DASHBOARD_CONFIG_KEY)

    if pre_state.goal:
        goal_json = json.dumps(pre_state.goal.model_dump(), ensure_ascii=False, indent=2)
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.GOAL_CURRENT_KEY,
            value=make_file_value(goal_json),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.GOAL_CURRENT_KEY)

    if pre_state.chapter:
        chapter_json = json.dumps(pre_state.chapter.model_dump(), ensure_ascii=False, indent=2)
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.CHAPTER_CURRENT_KEY,
            value=make_file_value(chapter_json),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.CHAPTER_CURRENT_KEY)

    if pre_state.forward_markers:
        markers_json = json.dumps(
            {"markers": [marker.model_dump(exclude_none=True) for marker in pre_state.forward_markers]},
            ensure_ascii=False,
            indent=2,
        )
        await store_client.put_item(
            ns,
            key=_STORE_CONTRACT.TIMELINE_MARKERS_KEY,
            value=make_file_value(markers_json),
        )
        logger.info("[%s] Populated %s", user_id, _STORE_CONTRACT.TIMELINE_MARKERS_KEY)


async def snapshot_store(store_client: Any, *, user_id: str = "user") -> StoreSnapshot:
    """抓取当前用户 namespace 的完整 Store 快照。"""
    ns = make_namespace(user_id)
    snapshot = StoreSnapshot()
    limit = 100
    offset = 0

    while True:
        result = await store_client.search_items(ns, limit=limit, offset=offset)
        items = result.get("items", []) if isinstance(result, dict) else result
        if not items:
            break

        for item in items:
            key = item.get("key") if isinstance(item, dict) else getattr(item, "key", None)
            value = item.get("value") if isinstance(item, dict) else getattr(item, "value", None)
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            try:
                content = unwrap_file_value(value)
            except Exception:
                content = json.dumps(value, ensure_ascii=False, indent=2)
            snapshot.files[key] = StoreFileArtifact(key=key, content=content, raw_value=value)

        if len(items) < limit:
            break
        offset += limit

    return snapshot


async def clear_store(store_client: Any, *, user_id: str = "user") -> None:
    """清空指定 namespace 下的所有 Store 项。"""
    ns = make_namespace(user_id)
    limit = 100
    deleted = 0

    while True:
        result = await store_client.search_items(ns, limit=limit, offset=0)
        items = result.get("items", []) if isinstance(result, dict) else result
        if not items:
            break

        for item in items:
            key = item.get("key") if isinstance(item, dict) else getattr(item, "key", None)
            if key:
                await store_client.delete_item(ns, key=key)
                deleted += 1

        if len(items) < limit:
            break

    if deleted:
        logger.info("[%s] Cleared %d items from Store", user_id, deleted)
