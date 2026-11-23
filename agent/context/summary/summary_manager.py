import json
import math
from typing import Sequence

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage, ToolMessage

from agent.context.token_count.token_count_result import TokenCountCompleteness, TokenCountAccuracy
from agent.context.token_count import TokenCounter
from agent.history import ConversationTurn
from agent.init import SummaryRuntimeConfig
from agent.profile import ProfileFactory
from config import settings, log
from config.settings import Setting
from exception import AgentException


class SummaryManager:

    def __init__(self):
        """初始化摘要管理器"""
        self.sys_prompt = settings.summary_sys_prompt
        self.runtime_config = self._init_runtime_config(settings)
        self.token_counter=TokenCounter()
        self.budget_config = settings.get_context_budget_config()

    @staticmethod
    def _init_runtime_config(setting: Setting) -> SummaryRuntimeConfig:
        """初始化独立摘要模型"""
        # 获取摘要模型配置
        profile_factory = ProfileFactory(setting)
        model_config, connection_config = profile_factory.get_model_configs(settings.summary_model)
        # 创建独立摘要模型
        model: BaseChatModel = init_chat_model(
            model=model_config.model_name,
            model_provider=connection_config.model_provider,
            api_key=connection_config.api_key.get_secret_value(),
            base_url=connection_config.base_url,
            temperature=connection_config.temperature,
            timeout=connection_config.timeout,
            max_retries=connection_config.max_retries
        )
        return SummaryRuntimeConfig(model=model, model_config=model_config, connection_config=connection_config)


    async def generate_summary(self, turns: Sequence[ConversationTurn]) -> str:
        """
        根据原始历史轮次重新生成完整摘要
        """
        if not turns:
            raise AgentException("摘要历史轮次不能为空")
        history_text=self._serialize_turns(turns)
        if not history_text.strip():
            raise AgentException("摘要历史内容不能为空")
        messages = [
            SystemMessage(content=self.sys_prompt),
            HumanMessage(content=f"请根据以下原始对话生成完整摘要：\n\n{history_text}")
        ]
        self._check_input_budget(messages)
        response = await self.runtime_config.model.ainvoke(messages)
        if not isinstance(response.content, str):
            raise AgentException("摘要模型返回了非文本内容")
        summary=response.content.strip()
        log.info(f"第前{len(turns)}轮次压缩获取到的摘要信息：{summary}")
        if not summary:
            raise AgentException("摘要模型返回内容为空")
        return summary

    def _serialize_turns(self,turns: Sequence[ConversationTurn]) -> str:
        """将完整历史轮次转换为摘要输入文本"""
        contents:list[str]=[]
        for index, turn in enumerate(turns, start=1):
            if not turn.is_complete:
                raise AgentException(f"第{index}轮历史尚未完成，不能参与摘要")
            contents.append(f"## 第{index}轮对话")
            for message in turn.messages:
                message_text=self._serialize_message(message)
                if message_text:
                    contents.append(message_text)
        return "\n\n".join(contents)

    def _serialize_message(self, message: BaseMessage) -> str:
        """序列化单条历史消息"""
        if isinstance(message, SystemMessage):
            return ""
        if isinstance(message, HumanMessage):
            return self._serialize_content("用户", message.content)
        if isinstance(message, AIMessage):
            parts = [self._serialize_content("助手", message.content)]
            if message.tool_calls:
                parts.append("助手工具调用：" + json.dumps(message.tool_calls, ensure_ascii=False, default=str))
            if message.invalid_tool_calls:
                parts.append("助手未解析工具调用："+json.dumps(message.invalid_tool_calls, ensure_ascii=False, default=str))
            return "\n".join(part for part in parts if part)
        if isinstance(message, ToolMessage):
            content = self._serialize_content(f"工具结果（{message.name or '未知工具'}）", message.content)
            return f"{content}\n工具调用ID：{message.tool_call_id}"
        raise AgentException(f"不支持的摘要消息类型：{type(message).__name__}")

    @staticmethod
    def _serialize_content(role:str, content: str|list) -> str:
        """序列化消息文本内容"""
        if not isinstance(content, str):
            raise AgentException(f"{role}包含非文本内容，当前摘要模块赞不支持多模态消息")
        if not content.strip():
            return ""
        return f"{role}:{content}"

    def _calculate_safety_tokens(self, token_result) -> int:
        """计算摘要请求的安全余量"""

        if token_result.accuracy == TokenCountAccuracy.EXACT:
            return self.budget_config.safety_base_tokens

        estimated_tokens = math.ceil(
            token_result.total_tokens * self.budget_config.safety_ratio
        )

        return self.budget_config.safety_base_tokens + estimated_tokens

    def _check_input_budget(
            self,
            messages: list[BaseMessage],
    ) -> None:
        """检查摘要模型输入是否满足上下文预算"""

        model_config = self.runtime_config.model_config
        connection_config = self.runtime_config.connection_config

        token_result = self.token_counter.count(
            messages=messages,
            model_config=model_config,
            connection_config=connection_config,
            tool_definitions=(),
            add_generation_prompt=True,
        )

        if token_result.completeness == TokenCountCompleteness.INCOMPLETE:
            raise AgentException("摘要模型输入Token统计不完整，无法进行预算判断")
        safety_tokens = self._calculate_safety_tokens(token_result)
        required_tokens = token_result.total_tokens + model_config.max_output_tokens + safety_tokens

        if required_tokens > model_config.context_window:
            raise AgentException(
                "摘要输入超过模型上下文预算："
                f"输入Token={token_result.total_tokens},"
                f"输出预留={model_config.max_output_tokens},"
                f"安全余量={safety_tokens},"
                f"上下文窗口={model_config.context_window}"
            )

    @staticmethod
    def calculate_covered_turn_count(
            complete_turns: Sequence[ConversationTurn],
            excluded_turns: Sequence[ConversationTurn],
            current_covered_count: int
    ) -> int:
        """计算本次摘要新的覆盖轮数"""
        if current_covered_count < 0:
            raise AgentException("当前摘要覆盖轮数不能小于0")
        if current_covered_count > len(complete_turns):
            raise AgentException("当前摘要覆盖轮数超过完整历史轮次")
        if not excluded_turns:
            return current_covered_count
        # 通过对象身份查找，避免dataclass值相等导致匹配错误
        excluded_indexes=[]
        for excluded_turn in excluded_turns:
            index = next((i for i, turn in enumerate(complete_turns)
                          if turn is excluded_turn),None)
            if index is None:
                raise AgentException("被裁剪的历史轮次不属于当前完整历史")
            excluded_indexes.append(index)
        # 不允许重复轮次
        if len(set(excluded_indexes)) != len(excluded_indexes):
            raise AgentException("被裁剪的历史轮次存在重复")
        excluded_indexes.sort()
        # 新裁剪的轮次必须紧接旧摘要覆盖边界
        expected_indexes = list(range(current_covered_count, current_covered_count+len(excluded_indexes)))
        if excluded_indexes != expected_indexes:
            raise AgentException("本次裁剪历史与当前摘要覆盖边界不连续")
        return current_covered_count + len(expected_indexes)


# history_text="""## 第1轮对话
#
# 用户:我是张三
#
# 助手:您好，张三！很高兴为您服务。请问有什么可以帮助您的吗？
#
# ## 第2轮对话
#
# 用户:https://bojieli.github.io/ai-agent-book/astro/#contents 你知道这本书户么？它是做什么的，值的我去学习么
#
# 助手工具调用：[{"name": "fetch_webpage_tool", "args": {"url": "https://bojieli.github.io/ai-agent-book/astro/#contents"}, "id": "call_edw86cpw", "type": "tool_call"}]
#
# 工具结果：(fetch_webpage_tool:{"success": true, "data": "网页 https://bojieli.github.io/ai-agent-book/astro/#contents 的内容：\n深入理解 AI Agent — 从原理到实践\n跳到正文\na\ni\nAI Agents\nin Depth\n全书目录\n配套实验\nGitHub\n简体中文\nEnglish\n简体中文\n✓\n繁體中文\nEspañol\nBahasa Indonesia\nРусский\nதமிழ்\nTiếng Việt\n日本語\n한국어\nالعربية\nTürkçe\nMagyar\nעברית\nPortuguês (Brasil)\n机器翻译 / Machine translation\n未经审核 / Not vetted\nFrançais\nMT\nDeutsch\nMT\nItaliano\nMT\nPolski\nMT\nNederlands\nMT\nУкраїнська\nMT\nČeština\nMT\nRomână\nMT\nΕλληνικά\nMT\nSvenska\nMT\nDansk\nMT\nSuomi\nMT\nNorsk\nMT\nไทย\nMT\nहिन्दी\nMT\n巴�লা\nMT\nBahasa Melayu\nMT\nFilipino\nMT\nKiswahili\nMT\nArabic\nMT\nفارسی\nMT\n一本开源书\n深入理解\nAI Agent.\n设计原理。\n工程实践。\n写给想理解 AI Agent 的开发者与探索者。\n具备基础编程知识更方便动手实验；第 1 章从概念讲起。\n开始阅读\n浏览目录\n↓\n作者：\n李博杰\n与开源社区\n智能体循环\n概念模型\nLLM\n推理引擎\n上下文\n任务 · 历史\n观察结果\n工具\n搜索 · 代码\nAPIs\n观察信息\n行动\n环境\n文件 · 浏览器 · 人\n决策，行动。\n环境变化\n推理\n行动\n观察\n暂停\n上下文为模型提供信息，工具让它影响世界。\n10\n章内容，从基础到系统\n15\n种语言版本\n↗\n开源，向所有人开放。\n从理解原理，到动手构建\n全书目录\n.\n从基础开始。\n沿着好奇心，继续探索。\n01\nAI Agent 入门\n模型、上下文、工具，以及将它们连接起来的循环。\n从这里开始\n02\n上下文工程\n构建有效的上下文，让智能体更好地完成任务。\n03\n用户记忆和知识库\n连接知识与记忆，让智能体有所依据。\n04\n工具\n为智能体提供可靠的工具接口，与世界交互。\n05\nCoding Agent 与通用 Agent\n把代码作为工具，创造新的能力。\n06\n交互：观测与动作空间的扩展\n将智能体延伸到语音、视觉、界面与长时任务。\n07\nAgent 的评估\n衡量行为、对比系统，从失败中学习。\n08\n模型后训练\n理解监督学习和强化学习如何塑造模型。\n09\nAgent 的持续进化\n把执行经验转化为持续的改进。\n10\n多 Agent 协作\n协调多个智能体，共享上下文，分解复杂任务。\n动手实践，让想法更清晰\n读懂它，再实现它。\n探索配套实验，阅读代码，构建自己的智能体。\n第 1 章配套实验\n深入理解 AI Agent\n开放共创，期待你的探索。\nApache 2.0", "msg": "成功"}
#
# 助手:是的，我知道这本书！这是一本关于 **AI Agent（人工智能智能体）** 的开源书籍，由李博杰编写。
#
# ## 📖 这本书是做什么的？
#
# 根据网页内容，这本书主要涵盖：
#
# 1. **核心主题**：深入理解 AI Agent 的设计原理和工程实践
# 2. **目标读者**：想理解 AI Agent 的开发者与探索者
# 3. **内容结构**：
#    - 从基础概念讲起（第 1 章）
#    - 涵盖 10 个章节，从入门到系统级应用
#    - 提供配套实验和代码实践
#
# ## 📚 主要内容包括：
#
# - **AI Agent 入门**：模型、上下文、工具及智能体循环
# - **上下文工程**：构建有效上下文让智能体更好完成任务
# - **用户记忆和知识库**：连接知识与记忆
# - **工具使用**：为智能体提供可靠工具接口
# - **Coding Agent**：把代码作为工具创造新能力
# - **交互扩展**：语音、视觉、界面与长时任务
# - **Agent 评估**：衡量行为、对比系统
# - **模型后训练**：监督学习和强化学习
# - **持续进化**：将执行经验转化为改进
# - **多 Agent 协作**：协调多个智能体
#
# ## 💡 是否值得学习？
#
# **值得学习的理由：**
#
# ✅ **开源免费**：Apache 2.0 协议，向所有人开放
# ✅ **15 种语言版本**：包括简体中文、英文等
# ✅ **理论与实践结合**：有配套实验和代码
# ✅ **系统性强**：从基础到高级的完整知识体系
# ✅ **实用性强**：涵盖当前 AI Agent 的核心技术和应用场景
#
# **适合人群：**
# - 对 AI Agent 感兴趣的开发者
# - 想构建智能体应用的工程师
# - 希望了解最新 AI 技术的研究者
#
# 如果您有编程基础，这本书会非常有帮助；即使没有，第 1 章也会从概念讲起。您可以根据兴趣选择阅读！""",
#
# messages = [
#     SystemMessage(content="""
#     # Role
#     你是一个专业的 AI Agent 上下文压缩器（Context Compressor），负责将历史对话压缩为精简、准确、结构化的上下文，使 Agent 能够在后续对话中保持用户认知和任务连续性。
#
#     你不是普通的对话总结器，而是负责维护用户长期信息、任务状态和历史决策的上下文管理器。
#
#     # Core Principles
#
#     压缩上下文时，必须遵循以下原则：
#
#     1. 信息准确性优先于压缩率。
#     2. 重要信息优先于信息长度。
#     3. 长期有效的信息优先于临时信息。
#     4. 用户明确表达的信息优先于模型推测。
#     5. 最新确认的决策优先于已经失效的历史决策。
#     6. 不得因为信息与当前任务无关，就直接删除具有长期价值的信息。
#
#     # Information Retention Strategy
#
#     ## 1. 用户身份信息（最高优先级）
#
#     必须尽可能完整地保留用户明确提供的身份和称呼信息，例如：
#
#     - 用户姓名、昵称和称呼偏好。
#     - 用户明确提供的职业、职位和角色。
#     - 用户明确提供的所属组织、团队或项目身份。
#     - 用户明确表达的其他长期身份信息。
#
#     要求：
#     - 不得随意修改用户姓名或称呼。
#     - 不得将推测的身份信息当作事实。
#     - 不得因为当前任务切换而删除这些信息。
#     - 如果用户主动更正身份信息，以最新明确的信息为准。
#
#     ## 2. 用户长期信息（高优先级）
#
#     保留对未来多个对话可能有帮助的信息，例如：
#
#     - 长期项目及其背景。
#     - 长期使用的技术栈和开发环境。
#     - 长期学习目标。
#     - 稳定的工作习惯和使用偏好。
#     - 用户明确要求长期遵守的规则。
#
#     这些信息不依赖当前任务，应尽可能跨任务保留。
#
#     ## 3. 用户偏好与约束（高优先级）
#
#     保留用户明确表达的偏好和限制，例如：
#
#     - 喜欢的回答风格和详细程度。
#     - 对代码结构、设计方式的偏好。
#     - 不希望采用的技术方案。
#     - 已经明确否决的方案。
#     - 用户要求后续持续遵守的行为规则。
#
#     特别注意：区分临时要求和长期要求，不得擅自扩大要求的适用范围。
#
#     ## 4. 当前任务信息（中高优先级）
#
#     保留：
#
#     - 当前任务的目标。
#     - 已经完成的工作。
#     - 当前执行进度。
#     - 已确定的技术方案。
#     - 尚未解决的问题。
#     - 下一步执行计划。
#
#     任务结束后，可以降低其优先级，但如果任务属于长期项目，仍应保留项目背景和重要决策。
#
#     ## 5. 临时对话信息（普通优先级）
#
#     包括：
#
#     - 一次性问题。
#     - 临时计算结果。
#     - 普通寒暄。
#     - 重复表达。
#     - 已经解决且不影响后续工作的细节。
#
#     在 Token 预算不足时，优先压缩或删除此类信息。
#
#     # Conflict Resolution
#
#     1. 用户最新明确表达的信息优先于旧信息。
#     2. 用户主动更正的信息优先于历史记录。
#     3. 已确认的决策优先于讨论中的假设。
#     4. 不得将用户提出的问题当成已经认可的结论。
#     5. 不得将计划中的操作记录为已经完成。
#     6. 无法确认的信息应标记为待确认，而不是自行推断。
#
#     # Compression Priority
#
#     当 Token 预算不足时，按照以下优先级分配保留空间：
#
#     P0：用户身份信息及明确的称呼要求。
#     P1：长期有效的用户信息、偏好和约束。
#     P2：长期项目背景及已确认的重要决策。
#     P3：当前任务目标、进度和待办事项。
#     P4：临时对话细节和中间过程。
#
#     优先压缩低优先级信息，不得为了提高压缩率而直接删除高优先级信息。
#
#     # Output Format
#
#     ## 1. 用户身份信息
#     记录用户明确提供的姓名、昵称、称呼及其他适合保留的身份信息。
#
#     ## 2. 用户长期信息
#     记录长期项目、技术栈、学习目标及其他长期有效的信息。
#
#     ## 3. 用户偏好与约束
#     记录用户明确表达的长期偏好、限制和行为要求。
#
#     ## 4. 项目背景与已确认决策
#     记录重要项目背景、技术架构、已确定的方案及其依据。
#
#     ## 5. 当前任务状态
#     记录任务目标、已完成工作、当前进度及尚未完成的事项。
#
#     ## 6. 待解决问题
#     记录未解决的问题、风险及需要确认的内容。
#
#     ## 7. 下一步计划
#     记录 Agent 后续应该执行的具体操作。
#
#     # Output Requirements
#
#     1. 只输出压缩后的上下文，不输出分析过程。
#     2. 严格区分事实、推测、待确认事项和已确认决策。
#     3. 保留姓名、称呼、技术标识符、文件路径和关键参数的原始表达。
#     4. 不得编造、推测或擅自补充用户信息。
#     5. 合并重复信息，但不能丢失不同信息之间的语义关系。
#     6. 不得将临时要求错误地升级为长期偏好。
#     7. 不得将用户明确要求保留的信息删除。
#     8. 输出必须能够独立使用，使没有阅读过原始对话的 Agent 能够理解用户背景并继续执行任务。
#     9. 在预算不足时，优先压缩低优先级信息，而不是删除高优先级信息。
#     """),
#
#     HumanMessage(content=f"请根据以下原始对话生成完整摘要：\n\n{history_text}")
# ]
# summary_manager = SummaryManager()
# response =  asyncio.run(summary_manager.runtime_config.model.ainvoke(messages))
# print(response.content)
