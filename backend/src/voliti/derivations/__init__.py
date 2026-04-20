# ABOUTME: 派生层聚合入口：由 PlanDocument 等契约派生为前端 / Briefing 视图对象
# ABOUTME: 纯函数、不做 Store / IO；输入展开后的 dict，避免上游 N+1

from voliti.derivations.plan_view import (
    DayTemplateItem,
    EventView,
    MapState,
    PlanViewRecord,
    WatchItem,
    WeekFreshness,
    compute_plan_view,
)

__all__ = [
    "compute_plan_view",
    "PlanViewRecord",
    "MapState",
    "EventView",
    "WeekFreshness",
    "DayTemplateItem",
    "WatchItem",
]
