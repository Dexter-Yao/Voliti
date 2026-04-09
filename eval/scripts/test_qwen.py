# ABOUTME: Qwen 3.6 Plus API 连通性验证脚本
# ABOUTME: 测试基础对话、tool calling、structured output 三项能力

import os
import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

# 加载 backend/.env 中的 DASHSCOPE_API_KEY
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ENV = os.path.join(_SCRIPT_DIR, "..", "..", "backend", ".env")
load_dotenv(_BACKEND_ENV)

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    print("错误：未找到 DASHSCOPE_API_KEY 环境变量")
    sys.exit(1)

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _create_model(**kwargs):
    """创建 Qwen 模型实例。

    默认禁用深度思考（enable_thinking=False），避免 reasoning token
    泄露为 ghost tool call。生产环境中可按需开启。
    """
    default_kwargs: dict = {"extra_body": {"enable_thinking": False}}
    default_kwargs.update(kwargs)
    return init_chat_model(
        "openai:qwen3.6-plus",
        base_url=BASE_URL,
        api_key=DASHSCOPE_API_KEY,
        **default_kwargs,
    )


def test_basic_chat():
    """测试 1: 基础中文对话。"""
    print("=" * 40)
    print("测试 1: 基础中文对话")
    print("=" * 40)
    model = _create_model()
    response = model.invoke("用一句话介绍你自己。")
    print(f"响应: {response.content}")
    print(f"类型: {type(response)}")
    assert response.content, "响应内容为空"
    print("✓ 通过\n")


def test_tool_calling():
    """测试 2: Tool calling（DeepAgent 硬依赖）。"""
    print("=" * 40)
    print("测试 2: Tool calling")
    print("=" * 40)

    from langchain_core.tools import tool

    @tool
    def get_weather(city: str) -> str:
        """获取指定城市的天气。"""
        return f"{city}：晴，25°C"

    model = _create_model()
    model_with_tools = model.bind_tools([get_weather])
    response = model_with_tools.invoke("上海今天天气怎么样？")

    print(f"响应: {response}")
    print(f"Tool calls: {response.tool_calls}")
    assert response.tool_calls, "未生成 tool call"
    # Qwen 可能生成多个 tool call，只需确认目标 tool 在其中
    tool_names = [tc["name"] for tc in response.tool_calls]
    assert "get_weather" in tool_names, f"get_weather 不在 tool calls 中: {tool_names}"
    weather_call = next(tc for tc in response.tool_calls if tc["name"] == "get_weather")
    assert "city" in weather_call["args"], f"缺少 city 参数: {weather_call['args']}"
    if response.invalid_tool_calls:
        print(f"⚠ 存在 {len(response.invalid_tool_calls)} 个 invalid tool calls（已知 Qwen 兼容性问题）")
    print("✓ 通过\n")


def test_structured_output():
    """测试 3: Structured output（JSON schema 输出）。"""
    print("=" * 40)
    print("测试 3: Structured output")
    print("=" * 40)

    class MoodAssessment(BaseModel):
        """用户情绪评估。"""
        energy: int = Field(ge=1, le=10, description="精力水平 1-10")
        mood: str = Field(description="情绪描述")
        needs_support: bool = Field(description="是否需要额外支持")

    model = _create_model()
    # DashScope 要求 json_object 模式时 messages 中包含 "json" 字样
    # 使用 method="function_calling" 通过 tool schema 实现 structured output
    structured_model = model.with_structured_output(MoodAssessment, method="function_calling")
    result = structured_model.invoke("用户说：'今天好累啊，什么都不想做。' 评估这个用户的状态。")

    print(f"结果: {result}")
    print(f"类型: {type(result)}")
    assert isinstance(result, MoodAssessment), f"返回类型不匹配: {type(result)}"
    assert 1 <= result.energy <= 10, f"energy 超出范围: {result.energy}"
    print("✓ 通过\n")


if __name__ == "__main__":
    tests = [test_basic_chat, test_tool_calling, test_structured_output]
    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"✗ 失败: {e}\n")
            failed += 1

    print("=" * 40)
    print(f"结果: {passed} 通过, {failed} 失败")
    if failed:
        print("⚠ 存在失败项，需评估是否影响 DeepAgent 集成")
        sys.exit(1)
    else:
        print("✓ 所有测试通过，Qwen 3.6 Plus 可接入")
