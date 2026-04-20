# ABOUTME: /timeline/markers.json 路径的 Pydantic 契约模型
# ABOUTME: MarkerItem 单条外部事件；MarkersRecord 列表容器

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class MarkerItem(BaseModel):
    id: str
    date: str
    timezone: str = "Asia/Shanghai"
    description: str = Field(min_length=2, max_length=100)
    risk_level: Literal["low", "medium", "high"] = "medium"
    status: Literal["upcoming", "passed", "cancelled"] = "upcoming"
    created_at: str
    linked_lifesign: str | None = None


class MarkersRecord(BaseModel):
    markers: list[MarkerItem]
