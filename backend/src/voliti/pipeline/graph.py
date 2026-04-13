# ABOUTME: 日终 Pipeline 的 LangGraph Graph 包装
# ABOUTME: 将 run_day_end_pipeline 包装为可被 Cron API 调度的 graph

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import StateGraph

from voliti.pipeline.day_end import run_day_end_pipeline
from voliti.store_contract import STORE_NAMESPACE_PREFIX

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """Pipeline graph 的 state schema。"""
    user_id: str
    results: dict[str, Any]


async def pipeline_node(state: PipelineState) -> dict[str, Any]:
    """执行日终 Pipeline 的 graph node。"""
    from langgraph_sdk import get_client

    user_id = state["user_id"]
    namespace = (STORE_NAMESPACE_PREFIX, user_id)

    client = get_client()
    result = await run_day_end_pipeline(
        client=client,
        user_id=user_id,
        namespace=namespace,
    )

    return {"results": result}


def build_pipeline_graph() -> Any:
    """构建日终 Pipeline graph。"""
    builder = StateGraph(PipelineState)
    builder.add_node("run_pipeline", pipeline_node)
    builder.set_entry_point("run_pipeline")
    builder.set_finish_point("run_pipeline")
    return builder.compile()


graph = build_pipeline_graph()
