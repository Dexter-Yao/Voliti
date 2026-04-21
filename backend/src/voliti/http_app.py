# ABOUTME: LangGraph Cloud custom_routes · Plan view 派生 endpoint
# ABOUTME: 前端通过 GET /plan-view/{user_id} 获取 { plan, plan_view }；派生层单一事实源（GAP 19）

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from langgraph.store.base import BaseStore
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from voliti.contracts.markers import MarkerItem, MarkersRecord
from voliti.derivations.plan_view import compute_plan_view
from voliti.store_contract import (
    COPING_PLANS_INDEX_KEY,
    InvalidStoreValueError,
    InvalidUserIDError,
    TIMELINE_MARKERS_KEY,
    make_plan_archive_namespace,
    make_user_namespace,
    parse_json_file_value,
    unwrap_file_value,
    validate_user_id,
)
from voliti.tools.plan_tools import read_current_plan_with_self_heal

logger = logging.getLogger(__name__)


def _parse_markers(raw_value: dict[str, Any] | None) -> dict[str, MarkerItem]:
    """从 /timeline/markers.json 解析出 {id: MarkerItem}；损坏降级为空 dict + WARN。"""
    if raw_value is None:
        return {}
    try:
        data = parse_json_file_value(raw_value)
        record = MarkersRecord.model_validate(data)
        return {mk.id: mk for mk in record.markers}
    except (InvalidStoreValueError, ValidationError, ValueError) as exc:
        logger.warning(
            "http_app: markers parse failed, returning empty dict",
            extra={"exception_type": type(exc).__name__},
        )
        return {}


def _parse_lifesigns(raw_value: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """从 /coping_plans_index.md 解析出 {id: {trigger}}。

    格式约定：`- ls_001: "trigger text" → response [status]`；损坏降级为空 dict。
    """
    if raw_value is None:
        return {}
    try:
        text = unwrap_file_value(raw_value)
    except InvalidStoreValueError:
        logger.warning("http_app: lifesigns envelope malformed, returning empty dict")
        return {}

    result: dict[str, dict[str, str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        parts = line[2:].split(":", 1)
        if len(parts) < 2:
            continue
        ls_id = parts[0].strip()
        rest = parts[1].strip()
        trigger = ""
        if '"' in rest:
            first_q = rest.index('"')
            if rest.count('"') >= 2:
                second_q = rest.index('"', first_q + 1)
                trigger = rest[first_q + 1 : second_q]
        if ls_id:
            result[ls_id] = {"trigger": trigger}
    return result


def build_plan_view_payload(
    store: BaseStore,
    user_id: str,
    today: date,
) -> dict[str, Any] | None:
    """读 Store + 派生 plan_view + 构造可 JSON 序列化的 { plan, plan_view } 字典。

    返回 None 表示用户尚未创建 Plan；解析异常走派生层 try-skip 降级。
    """
    user_namespace = make_user_namespace(user_id)
    archive_namespace = make_plan_archive_namespace(user_id)

    plan = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)
    if plan is None:
        return None

    markers_raw: dict[str, Any] | None = None
    lifesigns_raw: dict[str, Any] | None = None
    try:
        markers_item = store.get(user_namespace, TIMELINE_MARKERS_KEY)
        markers_raw = markers_item.value if markers_item else None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "http_app: failed to read markers",
            extra={"exception_type": type(exc).__name__},
        )
    try:
        lifesigns_item = store.get(user_namespace, COPING_PLANS_INDEX_KEY)
        lifesigns_raw = lifesigns_item.value if lifesigns_item else None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "http_app: failed to read coping_plans_index",
            extra={"exception_type": type(exc).__name__},
        )

    markers = _parse_markers(markers_raw)
    lifesigns = _parse_lifesigns(lifesigns_raw)

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
        payload = build_plan_view_payload(store, user_id, today)
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
