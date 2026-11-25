# Agent 整体架构

> 本文档记录项目整体架构、模块职责、核心调用链、设计边界、实现状态和架构风险。
>
> 项目总体信息见 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)，全局协作规范见 [AGENTS.md](AGENTS.md)。
>
> **代码事实来源：** 项目主线以 `master` 实际源码为准；章节实验以对应章节分支实际源码为准。
>
> **审计日期：** 2026-11-25。未在对应源码中验证的能力不标记为已实现。

## 一、架构概览

当前 Agent 主要由应用执行、Agent 创建、上下文管理、会话管理、对话执行和工具系统组成。

```text
应用入口
  |
  v
AgentExecutor
  |
  +----------------------+
  |                      |
  v                      v
Profile / 配置组装       Session
  |
  v
AgentFactory
  |
  v
AgentRuntimeConfig
  |
  +--> LangChain ChatModel
  +--> LangChain Agent
  +--> System Prompt
  +--> Tools
  |
  v
ContextManager <------ Session.history / summary_state
  |
  +--> TokenCounter / TokenizerProvider
  +--> HistoryTurnParser
  +--> SummaryManager
  |
  v
AgentContext
  |
  v
ConversationHandler
  |
  +--> Agent.astream()
  +--> 工具调用事件处理
  +--> 最终回答提取
  +--> 消息写回 Session
  |
  v
用户响应
```

当前通过 LangChain `init_chat_model()` 初始化 ChatModel，并使用 `create_agent()` 创建 Agent。

项目技术栈目标包含 LangGraph，但当前代码没有显式构建自定义 StateGraph 工作流。不能将 LangChain Agent 内部可能使用的实现机制等同于项目已完成自定义 LangGraph 编排。

## 二、核心模块与职责

### 2.1 应用入口与执行协调

主要文件：

- `main/agent_mian.py`
- `main/agent_executor.py`

应用入口负责初始化依赖、选择 Agent Profile 和 Session，并接收用户请求。

AgentExecutor 是请求级协调入口，主要负责：

- 校验用户问题并创建 HumanMessage。
- 获取本轮 Agent 运行配置。
- 调用 ContextManager 构建上下文。
- 调用 ConversationHandler 执行 Agent。

Token 统计、摘要和工具底层访问不属于 AgentExecutor 的职责。

### 2.2 Profile 与配置组装

主要文件：

- `config/settings.py`
- `agent/model/model_config.py`
- `agent/model/model_connection_config.py`
- `agent/profile/agent_profile.py`
- `agent/profile/agent_profile_registry.py`
- `agent/profile/profile_factory.py`

主要职责：

- Setting：从环境变量和配置文件加载应用配置。
- ModelConfig：描述模型名称、上下文窗口、最大输出 Token 和 Tokenizer 配置等模型能力信息。
- ModelConnectionConfig：描述 Provider、API Key、Base URL、Temperature、Timeout 和重试次数等连接参数。
- AgentProfile：组织模型配置、连接配置、系统提示词和工具集合。
- ProfileFactory：创建 AgentProfileRegistry，并解析工具名称。

ProfileFactory 负责 Profile 组装，不负责创建和缓存 Agent。

### 2.3 AgentFactory 与运行时配置

主要文件：

- `agent/factory/agent_factory.py`
- `agent/init/agent_runtime_config.py`
- `agent/init/init_agent.py`

AgentFactory 根据 Profile 中的模型、连接、Prompt 和工具配置创建缓存键，并管理 Agent 实例。

当前实现：

- 使用 OrderedDict 实现有界 LRU 缓存。
- 使用 RLock 保护缓存访问。
- 相同配置复用 Agent，不同配置创建独立 Agent。
- API Key 使用 SHA-256 指纹参与缓存键，不将密钥原文放入缓存键。
- 返回 AgentRuntimeConfig，供请求后续流程使用。

Agent 初始化通过 LangChain `init_chat_model()` 和 `create_agent()` 完成。

### 2.4 上下文管理

主要目录：`agent/context/`

ContextManager 负责构建本轮 AgentContext，主要包括：

- 校验输入及模型上下文配置。
- 统计系统提示词、工具定义、当前输入和历史消息 Token。
- 计算输出预留与安全余量。
- 解析并选择完整历史轮次。
- 必要时协调 SummaryManager。
- 组装 AgentContext 并检查预算。

详细设计、技术决策、实现状态和已知问题见 [book/chapter2/上下文管理.md](book/chapter2/上下文管理.md)。

### 2.5 Session 会话管理

主要文件：`agent/session/session.py`

Session 当前保存：

- `session_id`
- 完整原始消息 `history`
- `summary_state`

`append_messages()` 只负责追加消息，不负责裁剪、删除或重排历史。

上下文筛选结果仅用于当前请求，不覆盖 Session 中的原始历史。

当前 Session 为内存对象，尚未实现数据库或其他持久化存储。

### 2.6 ConversationHandler 对话执行

主要文件：`agent/conversation/conversation_handler.py`

ConversationHandler 负责：

1. 校验本轮请求消息。
2. 调用 Agent 的异步流式接口 `astream()`。
3. 消费 messages 和 values 事件并输出文本片段。
4. 识别 AIMessage 中的工具调用。
5. 根据 tool_call_id 关联 ToolMessage 工具结果。
6. 检查 Agent 返回消息是否保留请求消息前缀。
7. 提取最终 AI 回复。
8. 成功执行后，将本轮完整新增消息追加到 Session。

当前代码在 Agent 执行失败时只追加本轮用户消息，然后重新抛出异常。

### 2.7 Tools 工具系统

主要目录：`agent/tool/`

当前工具层采用以下分层：

```text
LangChain Tool
    |
    v
Service
    |
    v
DAO
    |
    v
Domain Model / ToolResponseModel
```

模块职责：

- Tool：通过 LangChain 工具接口向 Agent 暴露名称、描述和参数。
- Service：处理业务调用、结果封装和异常转换。
- DAO：访问文件系统、外部网络或系统资源。
- Domain：定义工具输入输出相关的数据模型。

当前工具覆盖天气、计算、时间、网页抓取、网络搜索、文件操作和系统信息/资源查询。准确的工具注册列表以 `agent/tool/tool.py` 中的实际注册内容为准。

**设计边界：** 工具分层不代表已经具备完整的企业级权限治理。文件目录沙箱、SSRF 防护、工具执行权限、审计、并发限制和超时策略仍需结合实际业务场景评估。

## 三、核心请求调用链

一次请求的主要执行过程：

1. 应用入口选择 AgentProfile 并获取 Session。
2. AgentExecutor 校验问题并创建 HumanMessage。
3. AgentFactory 根据 Profile 获取或创建 AgentRuntimeConfig。
4. ContextManager 根据 Session 原始历史构建 AgentContext。
5. ConversationHandler 调用 Agent 的 `astream()` 接口。
6. Agent 根据系统提示词、上下文和工具定义生成回复或发起工具调用。
7. LangChain Agent 执行工具调用，ConversationHandler 处理并展示调用及结果事件。
8. ConversationHandler 校验返回消息、提取最终回答，并将本轮完整消息追加到 Session。
9. AgentExecutor 返回最终回答。

**关键边界：** ContextManager 选择历史是为了构建本轮模型输入；Session 保存原始消息是为了保留会话记录。两者不能混为一谈。

## 四、关键设计边界

### 4.1 当前上下文、用户记忆与企业知识库

| 信息类型 | 主要职责 | 当前状态 |
|---|---|---|
| 当前上下文 | 支撑当前请求和正在进行的对话 | 已实现文本上下文管理 |
| 会话历史与摘要 | 支撑同一 Session 内的历史连续性 | 已实现内存态历史和摘要状态 |
| 用户长期记忆 | 跨 Session 保存与用户有关的长期信息 | 尚未实现，正在学习第三章 |
| 企业知识库 | 提供组织共享、受权限约束的知识检索 | 尚未实现，正在学习 RAG 相关内容 |

Session.history 和 SummaryState 不等于用户长期记忆；Web Search / Web Fetcher 也不等于企业 RAG 知识库。

### 4.2 LangChain 与 LangGraph

- 当前模型调用使用 LangChain ChatModel。
- 当前 Agent 通过 LangChain `create_agent()` 创建。
- 项目目标技术栈包含 LangGraph。
- 当前代码没有显式创建自定义 StateGraph，因此自定义 LangGraph 工作流尚未实现。

### 4.3 上下文预算与模型输出限制

ModelConfig 中的 `max_output_tokens` 参与上下文预算计算，用于输出预留。

但当前 Agent 初始化代码没有显式将其传入模型生成参数。

因此，上下文预算中的输出预留不能等同于模型实际生成长度限制。

## 五、当前实现状态

| 模块 / 能力 | 状态 | 说明 |
|---|---|---|
| Profile 配置和注册 | 已实现 | ProfileFactory 组装 ProfileRegistry |
| Agent 创建 | 已实现 | LangChain init_chat_model + create_agent |
| Agent 缓存 | 已实现 | AgentFactory 有界 LRU 与锁 |
| 请求执行入口 | 已实现 | AgentExecutor |
| 文本上下文构建 | 已实现 | ContextManager |
| Token 统计 | 已实现（有边界） | 当前使用 Hugging Face TokenizerProvider |
| 历史轮次解析 | 已实现 | HistoryTurnParser |
| 摘要生成 | 已实现（有边界） | SummaryManager，处理文本历史 |
| Session 原始历史 | 已实现（内存） | 尚无持久化 |
| 工具分层 | 已实现 | Tool / Service / DAO / Domain |
| 用户长期记忆 | 未实现 | 第三章学习阶段 |
| 企业知识库 / RAG | 未实现 | 尚未完成理论学习和选型 |
| 自定义 LangGraph StateGraph | 未实现 | 当前没有显式 Graph 构建代码 |
| 企业级权限与工具治理 | 尚不完整 | 需结合业务需求设计 |

## 六、架构风险与待评估事项

以下问题来自静态代码审查，不代表已经确定具体修复方案：

1. **首轮上下文预算检查：** ContextManager 首轮空历史分支直接返回 AgentContext，绕过与后续轮次一致的预算检查。
2. **模型输出长度限制：** `max_output_tokens` 参与上下文预算预留，但没有显式限制实际模型生成长度。
3. **多模态支持：** TokenizerProvider 当前只处理文本内容，多模态 Token 统计尚未实现。
4. **Tokenizer 扩展性：** TokenCounter 当前只有 Hugging Face TokenizerProvider，未发现通用 Provider 兜底。
5. **Session 持久化：** Session 仅保存在内存中，进程退出后不能自动恢复会话。
6. **工具安全治理：** 文件目录沙箱、SSRF 防护、权限、审计、超时和并发限制仍需进一步完善。
7. **长期记忆与知识检索：** 当前没有已落地的用户长期记忆和企业 RAG 能力。

上述事项属于风险和待评估方向，不代表已确认的改造计划。

## 七、相关文档

| 文档 | 职责 |
|---|---|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | 项目总览、技术栈、实现状态摘要和文档索引 |
| [AGENTS.md](AGENTS.md) | 仓库协作约定和开发规范 |
| [book/chapter2/上下文管理.md](book/chapter2/上下文管理.md) | 第二章上下文工程的详细设计、决策和实现状态 |
| [book/chapter3/用户记忆和知识库.md](book/chapter3/用户记忆和知识库.md) | 第三章学习路线、用户记忆和企业知识库 |
