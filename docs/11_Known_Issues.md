<!-- ABOUTME: Voliti 已知问题清单，记录当前确认存在且暂不阻断发布的问题 -->
<!-- ABOUTME: 本文只保留问题边界、当前影响、升级条件与跟踪入口 -->

# Voliti 已知问题

## 1. DeepAgents FilesystemMiddleware `context` 序列化 warning

**状态**

- 类型：上游依赖 warning
- 当前结论：非阻断，继续观察

**现象**

backend 的 tools 节点偶发如下 warning：

```text
PydanticSerializationUnexpectedValue(
  Expected 'none' ... [field_name='context', input_type=dict]
)
```

**当前影响**

在默认运行模式下，该 warning **不会影响产品实际运行**。当前已确认不阻断：

1. backend 启动
2. Coach graph 加载
3. A2UI interrupt 触发与恢复
4. live eval 正常执行

**问题边界**

1. 根因位于上游依赖链，不在 Voliti 业务逻辑。
2. 触发面集中在 `FilesystemMiddleware` 生成的 `read_file`、`ls` 等工具。
3. 该问题当前属于日志噪音，不是功能性错误。

**升级条件**

出现以下任一情况时，必须转入正式修复：

1. warning 导致 tools 节点真实失败
2. backend 默认运行稳定性受影响
3. live eval 或 CI 因该 warning 产生失败
4. 上游发布明确修复版本，且升级成本可控

**跟踪入口**

- 上游 issue：
  - [deepagents #491](https://github.com/langchain-ai/deepagents/issues/491)
  - [deepagents #2249](https://github.com/langchain-ai/deepagents/issues/2249)
  - [langchain #34770](https://github.com/langchain-ai/langchain/issues/34770)
  - [langchain PR #34771](https://github.com/langchain-ai/langchain/pull/34771)
- 本地证据：
  - [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py)
  - [`backend/src/voliti/middleware/briefing.py`](../backend/src/voliti/middleware/briefing.py)
  - [`eval/src/voliti_eval/client.py`](../eval/src/voliti_eval/client.py)
