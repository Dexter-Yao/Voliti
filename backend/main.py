# ABOUTME: Voliti 应用入口
# ABOUTME: 初始化配置并创建 Coach Agent

from pathlib import Path

from voliti.bootstrap import init
from voliti.agent import create_coach_agent

PROJECT_ROOT = Path(__file__).parent


def main() -> None:
    """创建 Coach Agent 并启动。"""
    init(PROJECT_ROOT)
    agent = create_coach_agent()
    print(f"Coach Agent 就绪: {agent.name}")


if __name__ == "__main__":
    main()
