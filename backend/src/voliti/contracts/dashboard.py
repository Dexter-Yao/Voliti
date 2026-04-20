# ABOUTME: /profile/dashboardConfig 路径的 Pydantic 契约模型
# ABOUTME: 前端 Mirror 指标卡片的渲染配置，与 Plan 内容分属

from __future__ import annotations

from pydantic import BaseModel


class NorthStarConfig(BaseModel):
    key: str
    label: str
    type: str
    unit: str | None = None
    delta_direction: str | None = None


class SupportMetric(BaseModel):
    key: str
    label: str
    type: str
    unit: str | None = None
    order: int | None = None


class DashboardConfigRecord(BaseModel):
    north_star: NorthStarConfig
    support_metrics: list[SupportMetric]
    user_goal: str | None = None
