# ABOUTME: LangGraph Cloud custom_routes · Plan view 派生 endpoint
# ABOUTME: 前端通过 GET /plan-view/{user_id} 获取 { plan, plan_view }；派生层单一事实源（GAP 19）

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any

from langgraph.store.base import BaseStore
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from voliti.contracts.plan import PlanDocument
from voliti.derivations.plan_store_parsers import parse_lifesigns_index, parse_markers
from voliti.derivations.plan_view import compute_plan_view
from voliti.store_contract import (
    COPING_PLANS_INDEX_KEY,
    InvalidStoreValueError,
    InvalidUserIDError,
    PLAN_CURRENT_KEY,
    TIMELINE_MARKERS_KEY,
    make_file_value,
    make_plan_archive_namespace,
    make_user_namespace,
    unwrap_file_value,
    validate_user_id,
)

logger = logging.getLogger(__name__)


async def _atry_read_current(
    store: BaseStore, user_namespace: tuple[str, ...]
) -> PlanDocument | None:
    """异步读 /plan/current.json；损坏或缺失返回 None（不抛），交由自愈逻辑处理。"""
    try:
        item = await store.aget(user_namespace, PLAN_CURRENT_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "http_app: failed to aget /plan/current.json",
            extra={"exception_type": type(exc).__name__},
        )
        return None
    if item is None or item.value is None:
        return None
    try:
        text = unwrap_file_value(item.value)
        return PlanDocument.model_validate_json(text)
    except (InvalidStoreValueError, ValidationError, ValueError) as exc:
        logger.warning(
            "http_app: /plan/current.json corrupted, will self-heal from archive",
            extra={"exception_type": type(exc).__name__},
        )
        return None


async def _aload_latest_archive(
    store: BaseStore, archive_namespace: tuple[str, ...]
) -> PlanDocument | None:
    """异步列 archive namespace 下全部 items，返回 version 最大且合法的 PlanDocument。"""
    try:
        items = await store.asearch(archive_namespace, limit=1000)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "http_app: failed to asearch archive namespace",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    latest: PlanDocument | None = None
    for item in items:
        if item.value is None:
            continue
        try:
            doc = PlanDocument.model_validate_json(unwrap_file_value(item.value))
        except (InvalidStoreValueError, ValidationError, ValueError) as exc:
            logger.error(
                "http_app: archive item corrupted, skipping",
                extra={
                    "archive_key": getattr(item, "key", None),
                    "exception_type": type(exc).__name__,
                },
            )
            continue
        if latest is None or doc.version > latest.version:
            latest = doc
    return latest


async def _aread_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
) -> PlanDocument | None:
    """HTTP endpoint 专用 async 版自愈读取。

    运行时 Store 在 async event loop 内只能走 aget/asearch（sync 接口会返回
    未 resolved future 触发 InvalidStateError）。plan_tools.read_current_plan_with_self_heal
    的 sync 版本仅用于 tool runtime 与单元测试路径。
    """
    current_doc = await _atry_read_current(store, user_namespace)
    archive_latest = await _aload_latest_archive(store, archive_namespace)

    if archive_latest is None:
        return current_doc

    if current_doc is None or archive_latest.version > current_doc.version:
        logger.warning(
            "http_app: self-heal triggered, rewriting current from archive",
            extra={
                "current_version": current_doc.version if current_doc else None,
                "archive_max_version": archive_latest.version,
                "plan_id": archive_latest.plan_id,
            },
        )
        try:
            await store.aput(
                user_namespace,
                PLAN_CURRENT_KEY,
                make_file_value(archive_latest.model_dump_json()),
            )
        except Exception as exc:  # noqa: BLE001
            # current 写入失败 → 仅日志，下次 tool 调用会再次自愈
            logger.warning(
                "http_app: self-heal current write failed",
                extra={"exception_type": type(exc).__name__},
            )
        return archive_latest

    return current_doc


async def build_plan_view_payload(
    store: BaseStore,
    user_id: str,
    today: date,
) -> dict[str, Any] | None:
    """读 Store + 派生 plan_view + 构造可 JSON 序列化的 { plan, plan_view } 字典。

    async 路径（runtime Store 强制 async）。返回 None 表示用户尚未创建 Plan；
    解析异常走派生层 try-skip 降级。
    """
    user_namespace = make_user_namespace(user_id)
    archive_namespace = make_plan_archive_namespace(user_id)

    plan = await _aread_current_plan_with_self_heal(
        store, user_namespace, archive_namespace
    )
    if plan is None:
        return None

    # 并行读 markers 与 lifesigns（两者之间无依赖；return_exceptions 保留
    # per-key fail-open 语义：一个读失败仍用另一个）
    markers_result, lifesigns_result = await asyncio.gather(
        store.aget(user_namespace, TIMELINE_MARKERS_KEY),
        store.aget(user_namespace, COPING_PLANS_INDEX_KEY),
        return_exceptions=True,
    )

    def _unwrap(result: Any, key_label: str) -> dict[str, Any] | None:
        if isinstance(result, BaseException):
            logger.warning(
                "http_app: failed to read %s",
                key_label,
                extra={"exception_type": type(result).__name__},
            )
            return None
        return result.value if result is not None else None

    markers_raw = _unwrap(markers_result, "markers")
    lifesigns_raw = _unwrap(lifesigns_result, "coping_plans_index")

    markers = parse_markers(markers_raw)
    lifesigns = parse_lifesigns_index(lifesigns_raw)

    view = compute_plan_view(plan=plan, today=today, markers=markers, lifesigns=lifesigns)

    return {
        "plan": plan.model_dump(mode="json"),
        "plan_view": view.model_dump(mode="json"),
    }


async def _resolve_store() -> BaseStore:
    """延迟解析 LangGraph 运行时 Store；仅在 endpoint 调用时 import。"""
    from langgraph_api.store import get_store as api_get_store  # noqa: PLC0415

    return await api_get_store()


async def plan_view_endpoint(request: Request) -> JSONResponse:
    """GET /plan-view/{user_id}?today=YYYY-MM-DD — 返回 PlanDocument + PlanViewRecord。"""
    raw_user_id = request.path_params.get("user_id", "")
    try:
        user_id = validate_user_id(raw_user_id)
    except InvalidUserIDError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    today_param = request.query_params.get("today")
    if today_param:
        try:
            today = date.fromisoformat(today_param)
        except ValueError:
            return JSONResponse(
                {"error": f"today 必须为 ISO 日期（YYYY-MM-DD），收到 {today_param!r}"},
                status_code=400,
            )
    else:
        today = datetime.now(timezone.utc).date()

    try:
        store = await _resolve_store()
    except Exception as exc:  # noqa: BLE001
        logger.exception("http_app: failed to resolve runtime store")
        return JSONResponse(
            {"error": f"Store 不可达：{type(exc).__name__}"},
            status_code=503,
        )

    try:
        payload = await build_plan_view_payload(store, user_id, today)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "http_app: plan_view computation failed",
            extra={"user_id": user_id, "today": today.isoformat()},
        )
        return JSONResponse(
            {"error": f"plan_view 派生失败：{type(exc).__name__}"},
            status_code=500,
        )

    if payload is None:
        return JSONResponse({"error": "Plan 尚未创建"}, status_code=404)

    return JSONResponse(payload, status_code=200)


app = Starlette(
    routes=[
        Route("/plan-view/{user_id}", plan_view_endpoint, methods=["GET"]),
    ]
)
