# ABOUTME: Store 强格式 JSON 路径的 Pydantic 契约模型聚合入口
# ABOUTME: 具名子模块承载各路径契约；本文件做 re-export 与 CANONICAL_EXAMPLES 绑定

from __future__ import annotations

from pydantic import BaseModel
from typing import Final

from voliti.contracts.dashboard import (
    DashboardConfigRecord,
    NorthStarConfig,
    SupportMetric,
)
from voliti.contracts.markers import MarkerItem, MarkersRecord


__all__ = [
    "MarkerItem",
    "MarkersRecord",
    "NorthStarConfig",
    "SupportMetric",
    "DashboardConfigRecord",
    "CANONICAL_EXAMPLES",
]


# 提供给 Coach 的最小合法格式示例；与模型类直接绑定，避免字符串键在重命名时静默漂移
# PlanDocument 的完整示例见 tests/contracts/fixtures/store/plan_current.value.json
CANONICAL_EXAMPLES: Final[dict[type[BaseModel], str]] = {
    MarkersRecord: (
        '{"markers":[{"id":"mk_001","date":"2026-04-20T00:00:00+08:00",'
        '"description":"出差上海","risk_level":"high","status":"upcoming",'
        '"created_at":"2026-04-19T10:00:00Z"}]}'
    ),
    DashboardConfigRecord: (
        '{"north_star":{"key":"weight_trend","label":"体重趋势","type":"numeric","unit":"kg"},'
        '"support_metrics":[{"key":"protein_days","label":"蛋白质达标天","type":"count"}]}'
    ),
}
