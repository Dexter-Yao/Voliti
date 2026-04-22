# ABOUTME: Planner 运行时共享读取逻辑
# ABOUTME: 统一 current/archive 自愈、跨 plan_id 权威选择与降级语义

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from langgraph.store.base import BaseStore
from pydantic import ValidationError

from voliti.contracts.plan import PlanDocument
from voliti.store_contract import (
    InvalidStoreValueError,
    PLAN_CURRENT_KEY,
    make_file_value,
    unwrap_file_value,
)

logger = logging.getLogger(__name__)

PlanDegradedReason = Literal[
    "no_plan",
    "plan_data_corrupted_recovered",
    "plan_data_corrupted_unrecovered",
]


@dataclass(frozen=True)
class PlanReadResult:
    plan: PlanDocument | None
    degraded_reason: PlanDegradedReason | None = None


def _plan_recency_key(plan: PlanDocument) -> tuple[datetime, int, str]:
    return (plan.revised_at, plan.version, plan.plan_id)


def _parse_plan_text(
    raw_value: dict[str, Any] | None,
    *,
    context: str,
    path_label: str,
) -> tuple[PlanDocument | None, bool]:
    if raw_value is None:
        return None, False
    try:
        text = unwrap_file_value(raw_value)
        return PlanDocument.model_validate_json(text), False
    except (InvalidStoreValueError, ValidationError, ValueError) as exc:
        logger.warning(
            "%s: %s corrupted",
            context,
            path_label,
            extra={"exception_type": type(exc).__name__},
        )
        return None, True


def _pick_authoritative_archive_plan(
    raw_items: list[tuple[str | None, dict[str, Any] | None]],
    *,
    context: str,
) -> PlanDocument | None:
    latest_by_plan_id: dict[str, PlanDocument] = {}
    for key, raw_value in raw_items:
        plan, corrupted = _parse_plan_text(
            raw_value,
            context=context,
            path_label=f"archive item {key or '<unknown>'}",
        )
        if corrupted or plan is None:
            continue
        existing = latest_by_plan_id.get(plan.plan_id)
        if existing is None or plan.version > existing.version:
            latest_by_plan_id[plan.plan_id] = plan
            continue
        if plan.version == existing.version and _plan_recency_key(plan) > _plan_recency_key(existing):
            latest_by_plan_id[plan.plan_id] = plan

    if not latest_by_plan_id:
        return None

    latest_per_plan = list(latest_by_plan_id.values())
    active_candidates = [plan for plan in latest_per_plan if plan.status == "active"]
    if active_candidates:
        return max(active_candidates, key=_plan_recency_key)
    return max(latest_per_plan, key=_plan_recency_key)


def _should_rewrite_current(
    current: PlanDocument | None,
    authoritative: PlanDocument,
) -> bool:
    if current is None:
        return True
    if current.plan_id != authoritative.plan_id:
        return True
    return authoritative.version > current.version


def _finalize_read_result(
    *,
    current: PlanDocument | None,
    current_corrupted: bool,
    authoritative: PlanDocument | None,
    rewrite_current: callable | None,
    context: str,
) -> PlanReadResult:
    if authoritative is None:
        if current is not None:
            return PlanReadResult(plan=current)
        if current_corrupted:
            logger.warning(
                "%s: unrecovered corrupted plan data",
                context,
                extra={"degraded_reason": "plan_data_corrupted_unrecovered"},
            )
            return PlanReadResult(
                plan=None,
                degraded_reason="plan_data_corrupted_unrecovered",
            )
        return PlanReadResult(plan=None, degraded_reason="no_plan")

    if not _should_rewrite_current(current, authoritative):
        return PlanReadResult(plan=current)

    logger.warning(
        "%s: self-heal triggered, rewriting current from archive",
        context,
        extra={
            "current_plan_id": current.plan_id if current else None,
            "current_version": current.version if current else None,
            "authoritative_plan_id": authoritative.plan_id,
            "authoritative_version": authoritative.version,
        },
    )
    if rewrite_current is not None:
        rewrite_current(authoritative)
    degraded_reason: PlanDegradedReason | None = None
    if current_corrupted:
        degraded_reason = "plan_data_corrupted_recovered"
    return PlanReadResult(plan=authoritative, degraded_reason=degraded_reason)


def load_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
    *,
    now: datetime | None = None,
    context: str = "plan_runtime",
) -> PlanReadResult:
    try:
        current_item = store.get(user_namespace, PLAN_CURRENT_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "%s: failed to read /plan/current.json",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        current_item = None
    current, current_corrupted = _parse_plan_text(
        current_item.value if current_item is not None else None,
        context=context,
        path_label="/plan/current.json",
    )

    try:
        archive_items = store.search(archive_namespace, limit=1000)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "%s: failed to list archive namespace",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        archive_items = []

    authoritative = _pick_authoritative_archive_plan(
        [
            (getattr(item, "key", None), getattr(item, "value", None))
            for item in archive_items
        ],
        context=context,
    )

    def _rewrite(plan: PlanDocument) -> None:
        try:
            store.put(
                user_namespace,
                PLAN_CURRENT_KEY,
                make_file_value(plan.model_dump_json(), now=now),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s: self-heal current write failed",
                context,
                extra={"exception_type": type(exc).__name__},
            )

    return _finalize_read_result(
        current=current,
        current_corrupted=current_corrupted,
        authoritative=authoritative,
        rewrite_current=_rewrite,
        context=context,
    )


def read_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
    *,
    now: datetime | None = None,
    context: str = "plan_runtime",
) -> PlanDocument | None:
    return load_current_plan_with_self_heal(
        store,
        user_namespace,
        archive_namespace,
        now=now,
        context=context,
    ).plan


async def aload_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
    *,
    now: datetime | None = None,
    context: str = "plan_runtime",
) -> PlanReadResult:
    try:
        current_item = await store.aget(user_namespace, PLAN_CURRENT_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "%s: failed to read /plan/current.json",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        current_item = None
    current, current_corrupted = _parse_plan_text(
        current_item.value if current_item is not None else None,
        context=context,
        path_label="/plan/current.json",
    )

    try:
        archive_items = await store.asearch(archive_namespace, limit=1000)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "%s: failed to list archive namespace",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        archive_items = []

    authoritative = _pick_authoritative_archive_plan(
        [
            (getattr(item, "key", None), getattr(item, "value", None))
            for item in archive_items
        ],
        context=context,
    )

    async def _rewrite(plan: PlanDocument) -> None:
        try:
            await store.aput(
                user_namespace,
                PLAN_CURRENT_KEY,
                make_file_value(plan.model_dump_json(), now=now),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s: self-heal current write failed",
                context,
                extra={"exception_type": type(exc).__name__},
            )

    async def _run_finalize() -> PlanReadResult:
        result = _finalize_read_result(
            current=current,
            current_corrupted=current_corrupted,
            authoritative=authoritative,
            rewrite_current=None,
            context=context,
        )
        if result.plan is authoritative and _should_rewrite_current(current, authoritative):
            await _rewrite(authoritative)
        return result

    return await _run_finalize()


async def aread_current_plan_via_client_with_self_heal(
    client: Any,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
    *,
    now: datetime | None = None,
    context: str = "plan_runtime",
) -> PlanReadResult:
    try:
        current_item = await client.store.get_item(user_namespace, PLAN_CURRENT_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "%s: failed to read /plan/current.json",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        current_item = None
    current_raw = current_item.get("value") if isinstance(current_item, dict) else None
    current, current_corrupted = _parse_plan_text(
        current_raw if isinstance(current_raw, dict) else None,
        context=context,
        path_label="/plan/current.json",
    )

    try:
        archive_result = await client.store.search_items(
            archive_namespace, limit=1000, offset=0
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "%s: failed to list archive namespace",
            context,
            extra={"exception_type": type(exc).__name__},
        )
        archive_result = {"items": []}
    archive_items = archive_result.get("items", []) if isinstance(archive_result, dict) else archive_result

    authoritative = _pick_authoritative_archive_plan(
        [
            (
                item.get("key") if isinstance(item, dict) else getattr(item, "key", None),
                item.get("value") if isinstance(item, dict) else getattr(item, "value", None),
            )
            for item in archive_items
        ],
        context=context,
    )

    async def _rewrite(plan: PlanDocument) -> None:
        try:
            await client.store.put_item(
                user_namespace,
                key=PLAN_CURRENT_KEY,
                value=make_file_value(plan.model_dump_json(), now=now),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s: self-heal current write failed",
                context,
                extra={"exception_type": type(exc).__name__},
            )

    result = _finalize_read_result(
        current=current,
        current_corrupted=current_corrupted,
        authoritative=authoritative,
        rewrite_current=None,
        context=context,
    )
    if result.plan is authoritative and _should_rewrite_current(current, authoritative):
        await _rewrite(authoritative)
    return result
