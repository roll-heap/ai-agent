# AI Agent 企业级项目上下文

> 项目总入口：记录项目概况、技术栈、分支事实来源、整体状态和文档索引。  
> 全局协作规范见 [AGENTS.md](AGENTS.md)，整体架构见 [agent架构.md](agent架构.md)，章节细节见对应专题文档。

**仓库：** https://github.com/roll-heap/ai-agent  
**主分支：** `master`  
**当前学习分支：** `chapter3`

## 一、项目概况

- 以《深入理解 AI Agent》为主要学习路线，通过理论学习和项目实践建设具备企业级落地能力的 Agent。
- 主要开发语言为 Python，结合 LangChain、LangGraph 和 Ollama 开展学习与实现。
- 项目持续关注正确性、可维护性、可测试性、安全性、可观测性和性能。
- 书籍地址：https://bojieli.github.io/ai-agent-book/astro/#contents

## 二、分支约定与事实来源

| 分支 | 用途 |
|---|---|
| `master` | 项目主线及已完成阶段的基准 |
| `chapter3` | 第三章用户记忆和知识库的学习、实验及工程实现 |
| 其他章节分支 | 根据任务所属阶段和仓库实际分支约定确定 |

各类信息的权威来源：

| 信息 | 权威来源 |
|---|---|
| 项目主线实现状态 | `master` 分支实际源码 |
| 章节实验实现状态 | 对应章节分支实际源码 |
| 章节学习进度、实验结果和决策 | 对应章节专题文档 |
| 全局协作规范 | [AGENTS.md](AGENTS.md) |
| 整体架构和模块职责 | [agent架构.md](agent架构.md) |
| 章节详细设计和实验过程 | 对应章节专题文档 |

设计文档不能单独证明功能已经实现。涉及实现状态时，必须检查目标分支实际源码及必要验证，不得混淆不同分支的状态。

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

项目文档曾记录以下本地模型名称：`qwen3.5:4b`、`openbmb/minicpm5:2b`、`qwen3.5:9b`。这些属于历史学习记录，不代表当前运行模型清单。具体实验使用的模型以对应实验记录为准。

实际连接参数从环境变量或配置加载，文档不得记录密钥等敏感信息。

## 四、整体实现状态

以下为最近一次项目实现状态审计记录，不代表本次重新审计了 `master` 分支源码。后续涉及实现状态时，必须以目标分支实际源码和验证结果为准。

**已有基础能力：**
- Agent Profile 组装与注册。
- 基于 LangChain 创建 Agent。
- AgentFactory 缓存。
- AgentExecutor 请求执行入口。
- ConversationHandler 流式执行及 Session 历史写回。
- ContextManager 文本上下文预算、历史选择和摘要协调。
- Session 内存态历史与摘要状态。
- Tool / Service / DAO / Domain 分层。

**尚未完成或实现不完整：**
- 自定义 LangGraph StateGraph 工作流。
- 用户长期记忆正式集成。
- 企业知识库 / RAG。
- 多模态 Token 统计和摘要。
- Session 持久化。
- 完整的企业级工具权限治理。

第二章上下文管理的具体实现状态、设计决策和已知问题见 [book/chapter2/上下文管理.md](book/chapter2/上下文管理.md)。

整体模块职责、调用链和架构风险见 [agent架构.md](agent架构.md)。

## 五、当前学习进度

学习进度以对应章节专题文档为准，本节只记录当前阶段概况。

| 章节 | 当前状态 | 详细记录 |
|---|---|---|
| 第二章：上下文工程 | 一期文本上下文管理学习与工程实现已完成 | [上下文管理.md](book/chapter2/上下文管理.md) |
| 第三章：用户记忆和知识库 | 正在学习 Advanced JSON Cards 理论，尚未进入对应代码实现 | [用户记忆和知识库.md](book/chapter3/用户记忆和知识库.md) |

第三章已完成的基础实验、暂停的实验、历史模型表现和未开展的评估任务，统一记录在第三章专题文档中，不在此处重复维护。

## 六、文档索引

```text
项目根目录/
├── AGENTS.md                       # 全局协作规范
├── PROJECT_CONTEXT.md              # 项目总览、状态和文档索引
├── agent架构.md                     # 整体架构、模块职责、调用链和风险
└── book/
    ├── chapter2/
    │   └── 上下文管理.md             # 第二章专题
    └── chapter3/
        └── 用户记忆和知识库.md       # 第三章专题
```

新章节专题文档按照 [AGENTS.md](AGENTS.md) 中的统一章节文档规范组织，各章可根据实际内容保留必要的特有结构。

## 七、协作入口

开始项目任务时：

1. 根据任务所属阶段确定目标分支。
2. 读取本文件和对应专题文档，确认当前进度。
3. 涉及实现状态时检查目标分支实际源码。
4. 按照 [AGENTS.md](AGENTS.md) 执行学习、实验、代码实现、验证和文档维护。
