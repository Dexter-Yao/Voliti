# ABOUTME: LangGraph Dev Server 入口
# ABOUTME: 暴露模块级 graph 变量，供 langgraph.json 引用

from pathlib import Path

from voliti.bootstrap import init
from voliti.agent import create_coach_agent

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

init(_PROJECT_ROOT)
graph = create_coach_agent()
