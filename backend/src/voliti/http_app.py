# ABOUTME: LangGraph Cloud custom_routes · Plan view 派生 endpoint
# ABOUTME: 前端通过 GET /plan-view/{user_id} 获取 { plan, plan_view }；派生层单一事实源（GAP 19）

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from langgraph.store.base import BaseStore
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from voliti.derivations.plan_store_parsers import parse_lifesigns_index, parse_markers
from voliti.derivations.plan_view import compute_plan_view
from voliti.store_contract import (
    COPING_PLANS_INDEX_KEY,
    InvalidUserIDError,
    TIMELINE_MARKERS_KEY,
    make_plan_archive_namespace,
    make_user_namespace,
    validate_user_id,
)
from voliti.tools.plan_tools import read_current_plan_with_self_heal

logger = logging.getLogger(__name__)


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
