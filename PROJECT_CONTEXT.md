# AI Agent 企业级项目上下文

> 本文档是项目总入口，记录项目背景、整体架构概况、当前实现状态、学习进度、重要约束和专题文档索引。模块级详细设计以对应专题文档为准。

**仓库：** https://github.com/roll-heap/ai-agent  
**主分支：** master  
**当前学习分支：** chapter3  
**分支用途：**  
- master：项目主线及已完成阶段的基准。  
- chapter3：第三章用户记忆和知识库的学习、实验及工程实现。  
**审计日期：** 2026-11-24  
**事实原则：** 代码实现状态以 master 分支实际代码为准；设计文档不能单独证明功能已经实现。本次审计为静态代码检查，未执行测试。

## 一、项目背景与目标

- 开发者为 Java 资深工程师，已完成 Python 基础学习，能够编写较复杂的 Python 代码。
- 以《深入理解 AI Agent》作为主要学习路线，结合项目实践建设具备企业级落地能力的 Agent。
- 书籍地址：https://bojieli.github.io/ai-agent-book/astro/#contents
- 项目不是一次性 Demo，持续关注模块职责、可维护性、安全、权限、可观测性、性能和自动化测试。

## 二、技术栈

| 技术 | 当前用途或状态 |
|---|---|
| Python | 项目主要开发语言，已使用 |
| LangChain | ChatModel、Agent、Message、Tool 等，已使用 |
| LangGraph | 目标技术栈之一；当前代码未显式构建自定义 StateGraph |
| Ollama | 本地模型运行环境，项目配置约定 |
| Pydantic / Pydantic Settings | 配置和数据模型 |
| Hugging Face Transformers | Tokenizer 加载和 Token 统计 |
| logcore | 日志及关联 ID |
| unittest | 单元测试 |

项目记录的本地模型：

- `qwen3.5:4b`
- `openbmb/minicpm5:latest`
- `qwen3.5:9b`

模型通过 Ollama 本地使用。实际连接参数从环境变量或配置文件加载；不要在文档中记录 API Key、访问令牌等敏感值。

## 三、整体架构概况

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

详细架构见 `agent架构.md`。

## 四、当前实现状态

### 4.1 已实现

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

### 4.2 尚未实现或实现不完整

- 自定义 LangGraph StateGraph 工作流：当前没有显式 Graph 构建代码。
- 用户长期记忆：尚未落地，正在学习第三章。
- 企业知识库 / RAG：尚未落地。
- 多模态 Token 统计和多模态摘要：当前 TokenizerProvider 只处理字符串文本。
- Session 持久化：当前为内存对象。
- OutputTokenBudgetEstimator：旧设计记录中的设计目标，当前代码未实现；当前预算直接使用 max_output_tokens 预留。
- 摘要质量检查器：尚未实现。
- 企业级工具权限治理：目录沙箱、SSRF 防护、审计、超时和并发限制仍需进一步评估。

### 4.3 已知问题

1. ContextManager 的首轮空历史分支直接返回 AgentContext，绕过与非首轮一致的预算检查。
2. max_output_tokens 参与上下文预算预留，但当前 Agent 初始化代码没有显式将其传入模型生成参数。
3. TokenCounter 当前只有 Hugging Face TokenizerProvider，没有通用 Provider 自动降级。
4. Session 未持久化，进程退出后不能自动恢复会话。

上下文管理详细设计、决策和问题见 `book/chapter2/上下文管理.md`。

## 五、重要技术约束

### 5.1 全章节书籍实验目标与范围约束（已确认）

所有章节实验均以《深入理解 AI Agent》对应章节明确提出的理论目标、实验目的、实验步骤、实验数据和评价方式为基础。项目建设企业级 Agent 是长期目标，但不能以此为由擅自扩展或改变书中实验。

1. 按书中实验顺序逐步推进，不擅自跳过、增加或重排实验步骤。
2. 不擅自修改书中或已确定的实验数据，不增加书中未要求的评价维度、评分规则、验收门槛或额外标准。
3. 当前技术栈适配仅用于在 Python、LangChain、LangGraph 和 Ollama 环境中落实原实验；必须说明必要的实现差异及其对结果的影响，不得改变实验目标和评价口径。
4. 企业级安全、可观测性、性能、治理等扩展内容，待对应书籍实验完成后单独讨论，不混入当前实验。
5. 区分书中结论、实际观察、测量结果和主观判断；未运行或未验证的内容不得标记为已完成。
6. 一次只推进当前步骤，由学习者手写实现；当前步骤验证通过后再继续。

第三章实验 3-2 的具体约束和执行记录见 `book/chapter3/用户记忆和知识库.md`。

1. 以《深入理解 AI Agent》的理论、模式和实验作为设计依据；先学习验证，再设计实现。
2. 不为了使用某个框架、数据库或组件而引入它。
3. 优先分析当前代码并复用已有能力，避免重复建设。
4. 严格区分已确认决策、待确认方案、暂缓事项和已实现能力。
5. 不把类名、目录名或文档中的设计目标当成实现证据。
6. 不将 LangChain Agent 描述为项目已实现自定义 LangGraph StateGraph。
7. Session 历史和摘要不等于用户长期记忆；Web Search / Web Fetcher 不等于企业 RAG。
8. 所有新增代码示例和代码实现必须添加必要的中文注释。
9. 未经用户明确确认，不改变已经确认的技术方案，不修改业务代码。

## 六、当前学习与开发进度

### 第二章：上下文工程

已完成一期文本上下文管理相关学习和工程实现。详细设计、历史决策、代码实现状态及待办见：

- `book/chapter2/上下文管理.md`

### 第三章：用户记忆和知识库

当前正在学习第三章，优先推进实验 3-2：用户记忆存储格式的工程对比。已完成记忆层次及四种存储格式的基础学习，并完成实验数据集、统一记忆管理抽象、Simple Notes 基础实现、Enhanced Notes 静态组织对比，以及使用本地 LLM 生成 Enhanced Notes 的单样例验证。

当前使用 `qwen3.5:4b` 生成了一条 94 字符的 Enhanced Notes，人工检查结果符合本次样例预期。生成结果已写入独立实验 JSON 文件，并已通过重新实例化管理器验证持久化重载；6 个原文关键词查询全部命中，5 个语义相近但不包含原文关键词的自然语言问题全部未命中。这验证了当前检索实现是内容和标签的大小写不敏感子字符串匹配，不具备语义检索能力。60 个用例的端到端评估、LLM Judge 评分及 Token/延迟/资源成本比较尚未开展。

尚未确定最终存储格式，也尚未实现完整的用户长期记忆系统。当前实验 3-2 已完成 Simple Notes 和 Enhanced Notes 已记录的基础实验步骤；下一步按书中顺序学习 JSON Cards。JSON Cards、Advanced JSON Cards 的实验实现，以及 60 个用例端到端评估、LLM Judge 评分和 Token/延迟/资源成本比较尚未完成。具体步骤、实验结果和未完成项见 `book/chapter3/用户记忆和知识库.md`。

全章节实验协作原则已确认：所有章节实验以书中对应章节的目标、步骤、数据和评价方式为准；不擅自扩展实验步骤、修改实验数据或增加评价标准；技术适配不得改变实验目标；企业级增强内容待书中实验完成后单独讨论。每次只推进一个步骤，由学习者手写实现并在验证通过后继续。详细规范见仓库根目录 `AGENTS.md`，第三章执行摘要见 `book/chapter3/用户记忆和知识库.md`。

第三章完整学习路线见：

- `book/chapter3/用户记忆和知识库.md`

### 当前工作分支

当前使用 `chapter3` 分支进行第三章学习和开发。

第三章涉及的学习进度、实验结果、技术决策、专题设计和工程实现，均以 `chapter3` 分支最新内容为准。第三章学习成果先在 `chapter3` 分支积累，后续是否合并到 `master`，根据阶段验收情况决定。

## 七、文档结构与职责

```text
项目根目录/
├── PROJECT_CONTEXT.md             # 项目总入口、现状、进度和索引
├── AGENTS.md                      # 仓库协作约定
├── agent架构.md                    # Agent 整体架构
└── book/
    ├── chapter2/
    │   └── 上下文管理.md            # 第二章上下文工程专题
    └── chapter3/
        └── 用户记忆和知识库.md      # 第三章学习路线与专题
```

| 文档 | 职责 |
|---|---|
| PROJECT_CONTEXT.md | 项目背景、技术栈、架构概况、实现状态、学习进度、约束和文档索引 |
| agent架构.md | Agent 整体架构、模块职责、请求调用链和实现边界 |
| book/chapter2/上下文管理.md | 上下文管理与压缩的详细设计、技术决策、实现状态和问题 |
| book/chapter3/用户记忆和知识库.md | 第三章学习路线、用户记忆、RAG 和企业知识组织 |
| AGENTS.md | 仓库内协作和代码工作约定 |

详细设计只在对应专题文档中维护；PROJECT_CONTEXT.md 只保留必要概况和索引，避免重复堆积。

## 八、后续协作规则

1. 继续项目时先读取本文件和用户指定的专题文档。
2. 涉及实现状态时检查 master 分支实际代码。
3. 区分已实现、部分实现、待确认、暂缓和未实现。
4. 尊重当前学习进度，不擅自跳过实验或进入编码阶段。
5. 先解释原理、调用链、数据结构、异常边界和工程权衡，再提供实现。
6. 任何改变已确认架构约束的建议，先说明原因并等待用户确认。
7. 文档优先增量更新，保留仍有效的历史决策和设计原因。
8. 未经用户确认，不修改 GitHub 仓库；获得确认后只修改明确涉及的文件。
9. 不在对话和文档中输出密钥、访问令牌或其他敏感值。
10. 完成一个知识点或实验后先复盘，再由用户决定下一步。
