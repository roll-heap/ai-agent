import math
from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from agent.context.domain import ContextBudgetConfig, SummeryState, HistorySelectionResult
from agent.context.context import AgentContext
from agent.context.token_count import TokenCountResult, TokenCountAccuracy
from agent.context.token_count.token_count_result import TokenCountCompleteness
from agent.context.token_count import TokenCounter
from agent.history import HistoryTurnParser, ConversationTurn
from agent.init import AgentRuntimeConfig
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
        budget_config: ContextBudgetConfig
    ):
        self.history_turn_parser = history_turn_parser
        self.token_counter = token_counter
        self.budget_config = budget_config

    def build_context(
            self,
            history: Sequence[BaseMessage],
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
        connection_config = runtime_config.connection_config
        log.info(f"当前模型: {model_config.model_name},上下文窗口: {model_config.context_window},最大输出: {model_config.max_output_tokens}")
        # 1、解析历史轮次
        turns = self.history_turn_parser.parse_turns(history)
        # 2、保留完整历史轮次
        complete_turns = [turn for turn in turns if turn.is_complete]
        candidate_turns = complete_turns[summary_state.covered_turn_count]
        # 3、根据预算筛选历史
        selection_result = self._select_history(
            complete_turns=candidate_turns,
            current_input=current_input,
            runtime_config=runtime_config,
        )
        # 4. 记录最终上下文统计结果
        log.info(f"最终输入Token: {selection_result.token_result.total_tokens},"
            f"保留历史轮次: {len(selection_result.retained_turns)},"
            f"裁剪历史轮次: {len(selection_result.excluded_turns)}"
        )
        return AgentContext(messages=selection_result.messages)

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
            complete_turns: list[ConversationTurn],
            current_input: HumanMessage,
            runtime_config:AgentRuntimeConfig,
    ) -> HistorySelectionResult:
        remaining_turns = list(complete_turns)
        excluded_turns: list[ConversationTurn] = []
        while True:
            history_messages=[message for turn in remaining_turns for message in turn.messages]
            agent_messages=[*history_messages, current_input]
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
            if not remaining_turns:
                raise AgentException("当前系统提示词、工具定义和用户输入已经超过模型上下文预算")
            # 从最旧的历史轮次开始裁剪
            excluded_turns.append(remaining_turns.pop(0))


    def _select_summary_turns(
            self,
            complete_turns: list[ConversationTurn],
            excluded_turns: list[ConversationTurn],
            summary_state: SummeryState
    ) -> list[ConversationTurn]:
        """
        选择需要重新生成摘要的完整历史轮次
        """
        # 本次没有新增裁剪，不需要更新摘要
        if not excluded_turns:
            return []
        # 计算新的摘要覆盖范围
        target_covered_count = summary_state.covered_turn_count + len(excluded_turns)
        if target_covered_count > len(complete_turns):
            raise AgentException("摘要覆盖范围超过完整历史轮次数量")
        # 从原始历史中获取完整前缀，重新生成摘要
        return complete_turns[:target_covered_count]
