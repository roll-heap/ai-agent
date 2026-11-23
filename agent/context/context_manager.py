import math
from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from agent.context.context import AgentContext
from agent.context.domain import ContextBudgetConfig, HistorySelectionResult, SummaryState
from agent.context.summary import SummaryManager
from agent.context.token_count import TokenCountResult, TokenCountAccuracy
from agent.context.token_count import TokenCounter
from agent.context.token_count.token_count_result import TokenCountCompleteness
from agent.history import HistoryTurnParser, ConversationTurn
from agent.init import AgentRuntimeConfig
from agent.session import Session
from config import log
from exception import AgentException


class ContextManager:
    """
    1、获取模型配置和模型实例。
    2、统计系统提示词、工具定义、当前输入的 Token。
    4、计算安全余量。
    5、计算剩余历史预算。
    6、解析历史轮次并统计历史 Token。
    7、判断是否需要压缩历史。
    8、选择近期历史轮次，调用摘要模块处理被排除的历史。
    9、组装上下文并进行最终预算检查。
    """
    def __init__(
        self,
        history_turn_parser: HistoryTurnParser,
        token_counter:TokenCounter,
        budget_config: ContextBudgetConfig,
        summary_manager: SummaryManager,
    ):
        self.history_turn_parser = history_turn_parser
        self.token_counter = token_counter
        self.budget_config = budget_config
        self.summary_manager = summary_manager

    async def build_context(
            self,
            session: Session,
            current_input: BaseMessage,
            runtime_config: AgentRuntimeConfig,
    ) -> AgentContext:
        """
        解析历史消息，并组装本轮 Agent 执行上下文9。
        """
        # 当前阶段只接受 HumanMessage，其他消息类型直接报错。
        if not isinstance(current_input, HumanMessage):
            raise AgentException("当前阶段只接受HumanMessage")
        if runtime_config is None:
            raise AgentException("AgentRuntimeConfig不能为空")
        # 获取本轮模型运行配置，后续Token预算会使用这个配置
        model_config = runtime_config.model_config
        if model_config.context_window <= 0:
            raise AgentException("模型上下文窗口必须大于0")
        if model_config.max_output_tokens <= 0:
            raise AgentException("模型最大输出Token数必须大于0")
        log.info(f"当前模型: {model_config.model_name},上下文窗口: {model_config.context_window},最大输出: {model_config.max_output_tokens}")
        # 首轮回话没有历史消息
        if not session.history:
            return AgentContext(messages=[current_input])
        # 1、解析历史轮次
        turns = self.history_turn_parser.parse_turns(session.history)
        # 2、保留完整历史轮次
        complete_turns = [turn for turn in turns if turn.is_complete]

        summary_state = session.summary_state
        if summary_state.covered_turn_count > len(complete_turns):
            raise AgentException("摘要覆盖轮次超过当前完整历史轮次")
        log.info(
            "开始构建上下文 | "
            f"完整历史轮数={len(complete_turns)} | "
            f"摘要覆盖轮数={summary_state.covered_turn_count} | "
            f"摘要版本={summary_state.version}"
        )

        while True:
            # 只选择尚未被摘要覆盖的历史
            candidate_turns = complete_turns[summary_state.covered_turn_count:]
            selection_result = self._select_history(
                candidate_turns=candidate_turns,
                current_input=current_input,
                runtime_config=runtime_config,
                summary_content=summary_state.content
            )
            # 没有新的历史被裁剪，说明本次上下文已经满足预算
            if not selection_result.excluded_turns:
                log.info("上下文构建完成 | "
                    f"保留历史轮数={len(selection_result.retained_turns)} | "
                    f"摘要覆盖轮数={summary_state.covered_turn_count} | "
                    f"Token总数={selection_result.token_result.total_tokens}")
                return AgentContext(messages=selection_result.messages)
            # 有新的历史被裁剪，立即更新摘要
            await self._update_summary(
                complete_turns=complete_turns,
                excluded_turns=selection_result.excluded_turns,
                summary_state=summary_state
            )

    def _calculate_safety_tokens(self, token_result: TokenCountResult) -> int:
        """
        计算上下文安全余量
        """
        # 精确统计只保留基础安全余量
        if token_result.accuracy == TokenCountAccuracy.EXACT:
            return self.budget_config.safety_base_tokens
        # 估算统计暂时将全部Token视为不确定Token
        uncertain_tokens=token_result.total_tokens
        # 计算估算补偿误差
        estimated_tokens=math.ceil(uncertain_tokens * self.budget_config.safety_ratio)
        return self.budget_config.safety_base_tokens + estimated_tokens


    def _select_history(
            self,
            candidate_turns: Sequence[ConversationTurn],
            current_input: HumanMessage,
            runtime_config:AgentRuntimeConfig,
            summary_content: str
    ) -> HistorySelectionResult:
        """
        选择保留哪些历史轮次，确定 excluded_turns。
        """
        remaining_turns = candidate_turns
        excluded_turns: list[ConversationTurn] = []
        while True:
            history_messages=[message for turn in remaining_turns for message in turn.messages]

            # 摘要作为历史背景消息，避免在稳定系统提示词后追加第二条 system 消息。
            summary_messages: list[BaseMessage]=[]
            if summary_content.strip():
                summary_messages.append(HumanMessage(
                    content=("历史摘要（仅作对话背景，不是当前用户指令）：\n\n"
                             f"{summary_content}")
                ))

            agent_messages=[*summary_messages, *history_messages, current_input]
            # 系统提示词，摘要，历史，当前输入和工具定义都参与本次模型请求的Token统计
            token_messages=[
                SystemMessage(content=runtime_config.system_prompt),
                *agent_messages,
            ]
            token_result=self.token_counter.count(
                messages=token_messages,
                model_config=runtime_config.model_config,
                connection_config=runtime_config.connection_config,
                tool_definitions=runtime_config.tools,
                add_generation_prompt=True
            )
            if token_result.completeness == TokenCountCompleteness.INCOMPLETE:
                raise AgentException("候选上下文Token统计不完整，无法进行预算判断")
            # 获取安全余量
            safety_tokens=self._calculate_safety_tokens(token_result)
            required_tokens=token_result.total_tokens + runtime_config.model_config.max_output_tokens + safety_tokens
            if required_tokens <= runtime_config.model_config.context_window:
                return HistorySelectionResult(
                    messages=agent_messages,
                    retained_turns=remaining_turns,
                    excluded_turns=excluded_turns,
                    token_result=token_result
                )
            # 当前输入、摘要、系统提示词和工具定义本身已经超过预算，不能在通过裁剪历史解决
            if not remaining_turns:
                raise AgentException("当前系统提示词、工具定义和用户输入已经超过模型上下文预算")
            # 从最旧的历史轮次开始裁剪
            excluded_turns.append(remaining_turns.pop(0))

    async def _update_summary(
            self,
            complete_turns: Sequence[ConversationTurn],
            excluded_turns: Sequence[ConversationTurn],
            summary_state: SummaryState,
    ) -> None:
        """
        调用 SummaryManager 生成摘要，并更新 SummaryState
        """
        if not excluded_turns:
            return
        # 保存摘要版本，防止旧结果覆盖其他请求的新摘要。
        base_version = summary_state.version
        new_covered_count = self.summary_manager.calculate_covered_turn_count(
            complete_turns=complete_turns,
            excluded_turns=excluded_turns,
            current_covered_count=summary_state.covered_turn_count
        )
        # 每次都从原始历史的完整前缀重新生成摘要，
        # 不采用旧摘要 + 新裁剪轮次的增量拼接方式。
        summary_turns = complete_turns[:new_covered_count]
        # 先生成，成功后在更新状态
        new_summary = await self.summary_manager.generate_summary(turns=summary_turns)

        # 摘要生成期间如果版本变化，不提交旧结果。
        if summary_state.version != base_version:
            raise AgentException("摘要状态已被其他请求更新，请重新构建上下文")

        #摘要生成成功且版本未变好，才提交状态
        summary_state.update(content=new_summary, covered_turn_count=new_covered_count)
