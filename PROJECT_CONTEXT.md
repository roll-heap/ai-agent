# AI Agent 企业级项目上下文

> 项目总入口：维护项目概况、技术栈、分支事实来源、整体实现状态和文档索引。通用协作规则见 [AGENTS.md](AGENTS.md)，详细架构见 [agent架构.md](agent架构.md)，章节细节见对应专题文档。

**仓库：** https://github.com/roll-heap/ai-agent  
**主分支：** `master`  
**当前学习分支：** `chapter3`  
**审计日期：** 2026-11-25

## 一、项目背景与目标

- 以《深入理解 AI Agent》为主要学习路线，通过理论学习和项目实践建设具备企业级落地能力的 Agent。
- 主要开发语言为 Python，结合 LangChain、LangGraph 和 Ollama 开展学习与实现。
- 项目持续关注正确性、可维护性、可测试性、安全性、可观测性和性能。
- 书籍地址：https://bojieli.github.io/ai-agent-book/astro/#contents

## 二、分支约定与事实来源

| 分支 | 用途 |
|---|---|
| `master` | 项目主线及已完成阶段的基准 |
| `chapter3` | 第三章用户记忆和知识库的学习、实验及工程实现 |
| 其他章节分支 | 以仓库实际分支约定和任务所属阶段为准 |

事实来源按信息类型划分：

| 信息 | 权威来源 |
|---|---|
| 项目主线实现状态 | `master` 分支实际源码 |
| 章节实验实现状态 | 对应章节分支实际源码 |
| 章节学习进度、实验结果和章节决策 | 对应章节分支的专题文档 |
| 全局协作、学习和代码规范 | [AGENTS.md](AGENTS.md) |
| 整体架构、模块职责和调用链 | [agent架构.md](agent架构.md) |
| 章节详细设计与实验过程 | 对应章节专题文档 |

设计文档不能单独证明功能已经实现。实现状态必须检查对应分支实际源码及必要验证；不同分支的状态不得混为一谈。

## 三、技术栈

| 技术 | 当前用途或状态 |
|---|---|
| Python | 项目主要开发语言 |
| LangChain | ChatModel、Agent、Message、Tool 等 |
| LangGraph | 目标技术栈之一；当前代码未显式构建自定义 StateGraph |
| Ollama | 本地模型运行环境 |
| Pydantic / Pydantic Settings | 配置和数据模型 |
| Hugging Face Transformers | Tokenizer 加载和文本 Token 统计 |
| logcore | 日志及关联 ID |
| unittest | 单元测试 |

项目文档曾记录以下本地模型名称：`qwen3.5:4b`、`openbmb/minicpm5:2b`、`qwen3.5:9b`。这些是学习记录，不作为当前运行模型清单或运行状态的保证；具体实验使用的模型应记录在对应实验记录中。实际连接参数从环境变量或配置加载，文档不得记录密钥等敏感值。

## 四、整体架构概况

当前主要调用链：

```text
应用入口
  -> AgentExecutor
  -> ProfileFactory / AgentProfile
  -> AgentFactory
  -> ContextManager
  -> AgentContext
  -> ConversationHandler
  -> LangChain Agent / Tools
  -> Session 写回完整消息历史
```

主要模块：

| 模块 | 职责 |
|---|---|
| main | 应用入口和请求执行协调 |
| agent/profile | Agent Profile 组装和注册 |
| agent/factory | 创建或复用 Agent Runtime |
| agent/init | 初始化 ChatModel、Agent 和运行配置 |
| agent/context | 当前请求上下文、Token 预算、历史选择和摘要 |
| agent/history | 将消息解析为完整对话轮次 |
| agent/session | 保存会话原始历史和摘要状态 |
| agent/conversation | 流式执行、工具事件处理和 Session 更新 |
| agent/tool | LangChain Tool、Service、DAO 和领域模型 |
| config / exception / common | 配置、日志、异常和通用基础设施 |
| tests | 当前上下文、摘要和 Tokenizer 相关测试 |

详细模块边界和风险见 [agent架构.md](agent架构.md)。

## 五、项目实现状态

以下状态是本分支文档最近一次静态代码审计记录；具体分支边界见第二节。未重新运行测试的项目，不据此宣称测试通过。

### 5.1 已实现

- Agent Profile 配置组装和注册。
- 基于 LangChain `init_chat_model` 与 `create_agent` 创建 Agent。
- AgentFactory 有界 LRU 缓存和缓存键指纹。
- AgentExecutor 请求执行入口。
- ConversationHandler 流式执行、工具调用事件识别、最终回答提取和 Session 历史写回。
- Session 内存态原始历史与摘要状态。
- ContextManager 文本上下文预算协调、完整轮次选择和摘要协调。
- Hugging Face TokenizerProvider 文本 Token 统计。
- SummaryManager 文本历史摘要及摘要输入预算检查。
- Tool / Service / DAO / Domain 分层。

### 5.2 尚未实现或实现不完整

- 自定义 LangGraph StateGraph 工作流。
- 用户长期记忆的正式项目集成。
- 企业知识库 / RAG。
- 多模态 Token 统计和多模态摘要。
- Session 持久化。
- OutputTokenBudgetEstimator 独立实现；当前预算直接使用 `max_output_tokens` 预留。
- 摘要质量检查器。
- 完整的企业级工具权限治理，包括目录沙箱、SSRF 防护、审计、超时和并发限制。

### 5.3 已知问题

1. ContextManager 首轮空历史分支直接返回 AgentContext，绕过与非首轮一致的预算检查。
2. `max_output_tokens` 参与上下文预算预留，但当前 Agent 初始化代码没有显式将其传入模型生成参数。
3. TokenCounter 当前只有 Hugging Face TokenizerProvider，没有通用 Provider 自动降级。
4. Session 未持久化，进程退出后不能自动恢复会话。

第二章上下文管理的详细设计、决策和问题见 [book/chapter2/上下文管理.md](book/chapter2/上下文管理.md)。

## 六、当前学习进度

### 第二章：上下文工程

已完成一期文本上下文管理相关学习和工程实现。详细设计、历史决策、代码实现状态及待办见 [book/chapter2/上下文管理.md](book/chapter2/上下文管理.md)。

### 第三章：用户记忆和知识库

当前学习分支为 `chapter3`，当前专题和实验进度以 [book/chapter3/用户记忆和知识库.md](book/chapter3/用户记忆和知识库.md) 为准。当前处于 Advanced JSON Cards 理论学习阶段；尚未完成该知识点系统总结和实验 3-2 对应实验步骤核对，尚未开展对应代码实现。

本分支专题记录的阶段性事实摘要：
- 60 个 YAML 用例、统一记忆管理抽象接口和 Simple Notes 基础实现已完成。
- Enhanced Notes 已完成静态表达对比、单样例 LLM 生成、持久化重载及关键词检索边界验证；当前检索不具备语义检索能力。
- JSON Cards 管理器 CRUD、持久化重载、单样例生成写入，以及偏好卡片相关/无关问题的人工使用验证已完成；不代表自动化测试通过。
- Enhanced Notes 和 JSON Cards 多轮订阅更新案例因本地模型运行耗时暂停，整体部分完成；转账更正案例仅完成理论分析，未运行模型。
- 60 个用例端到端评估、LLM Judge 评分及 Token、延迟和资源成本比较尚未开展。
- Contextual Retrieval 仅为提前预览，不计入正式学习进度。

以上是章节专题记录的摘要，不替代专题中的详细实验记录，也不代表第三章全部实现已集成到项目主线。

## 七、文档索引与职责

```text
项目根目录/
├── AGENTS.md                       # 全仓库通用协作规范
├── PROJECT_CONTEXT.md              # 项目总览、分支事实来源、状态和索引
├── agent架构.md                     # 整体架构、模块职责、调用链和风险
└── book/
    ├── chapter2/
    │   └── 上下文管理.md             # 第二章专题
    └── chapter3/
        └── 用户记忆和知识库.md       # 第三章专题
```

新章节专题文档按 [AGENTS.md](AGENTS.md) 中的统一章节文档规范组织；各章允许按书籍内容保留特有结构。

## 八、协作入口

- 开始项目任务时，先按任务所属阶段确定分支，再读取本文件和对应专题文档。
- 涉及实现状态时检查该分支实际源码；不得默认所有章节状态均以 `master` 为准。
- 学习顺序、实验准入、代码交付、验证及文档维护规则统一见 [AGENTS.md](AGENTS.md)。
- 章节详细进度和实验结果只在对应专题文档中维护，避免多处重复。
