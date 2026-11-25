# AI Agent 企业级项目上下文

> 项目总入口：记录项目概况、技术栈、分支事实来源、整体状态和文档索引。全局规范见 [AGENTS.md](AGENTS.md)，整体架构见 [agent架构.md](agent架构.md)，章节细节见对应专题文档。

**仓库：** https://github.com/roll-heap/ai-agent  
**主分支：** `master`  
**当前学习分支：** `chapter3`

## 一、项目概况

- 以《深入理解 AI Agent》为主要学习路线，通过理论学习和项目实践建设具备企业级落地能力的 Agent。
- 主要开发语言为 Python，结合 LangChain、LangGraph 和 Ollama 开展学习与实现。
- 项目持续关注正确性、可维护性、可测试性、安全性、可观测性和性能。
- 全书学习聚焦知识点原理、适用场景和代码应用；不强制复现书籍性能指标或大规模评测，允许独立学习项目尚未采用的新技术，不要求必须集成项目。详见 [AGENTS.md](AGENTS.md)。
- 书籍地址：https://bojieli.github.io/ai-agent-book/astro/#contents

## 二、分支与事实来源

| 分支 | 用途 |
|---|---|
| `master` | 项目主线及已完成阶段的基准 |
| `chapter3` | 第三章用户记忆和知识库的学习、实验及工程实现 |
| 其他章节分支 | 按任务所属阶段和仓库实际约定确定 |

| 信息 | 权威来源 |
|---|---|
| 项目主线实现状态 | `master` 实际源码 |
| 章节实验实现状态 | 对应章节分支实际源码 |
| 章节学习进度与决策 | 对应章节专题文档 |
| 实验详细过程与结果 | 对应章节实验记录文档（如有） |
| 全局规范 | [AGENTS.md](AGENTS.md) |
| 整体架构 | [agent架构.md](agent架构.md) |

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

项目文档曾记录 `qwen3.5:4b`、`openbmb/minicpm5:2b`、`qwen3.5:9b` 等本地模型名称，仅为历史记录，不代表当前运行模型清单。具体实验模型以对应记录为准。文档不得记录密钥等敏感信息。

## 四、整体实现状态

以下为历史实现状态审计摘要，不代表本次重新审计了 `master` 源码。后续涉及实现状态时，必须以目标分支实际源码和验证结果为准。

**已有基础能力：**
- Agent Profile 组装与注册、基于 LangChain 创建 Agent、AgentFactory 缓存。
- AgentExecutor 请求执行入口、ConversationHandler 流式执行及 Session 历史写回。
- ContextManager 文本上下文预算、历史选择和摘要协调；Session 内存态历史与摘要状态。
- Tool / Service / DAO / Domain 分层。

**尚未完成或实现不完整：**
- 自定义 LangGraph StateGraph 工作流、用户长期记忆正式集成、企业知识库 / RAG。
- 多模态 Token 统计和摘要、Session 持久化、完整的企业级工具权限治理。

第二章具体状态见 [上下文管理.md](book/chapter2/上下文管理.md)，整体模块职责和架构风险见 [agent架构.md](agent架构.md)。

## 五、当前学习进度

学习进度以对应章节专题文档为准。

| 章节 | 当前状态 | 详细记录 |
|---|---|---|
| 第二章：上下文工程 | 一期文本上下文管理学习与工程实现已完成 | [上下文管理.md](book/chapter2/上下文管理.md) |
| 第三章：用户记忆和知识库 | 正在学习 Advanced JSON Cards 理论，尚未进入对应代码实践 | [用户记忆和知识库.md](book/chapter3/用户记忆和知识库.md) |

第三章历史实验过程和结果见 [实验记录.md](book/chapter3/实验记录.md)，日常学习无需默认加载该文件。

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
        ├── 用户记忆和知识库.md       # 第三章学习入口与当前进度
        └── 实验记录.md               # 第三章历史实验详情，按需读取
```

## 七、协作入口

开始项目任务时，确定目标分支，读取本文件和对应专题文档；涉及历史实验再读取实验记录，涉及实现状态则检查目标分支源码。学习、代码实践和文档维护遵循 [AGENTS.md](AGENTS.md)。
