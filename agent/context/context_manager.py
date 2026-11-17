from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from agent.context.context import AgentContext
from agent.history import HistoryTurnParser
from agent.init import AgentRuntimeConfig
from config import log
from exception import AgentException


class ContextManager:
    """
    1、获取模型配置和模型实例。
    2、统计系统提示词、工具定义、当前输入的 Token。
    3、调用 OutputTokenBudgetEstimator，计算输出预算。
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
    ):
        self.history_turn_parser = history_turn_parser

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
        system_prompt = runtime_config.system_prompt
        agent_tools = runtime_config.tools
        log.info(f"当前模型: {model_config.model_name},上下文窗口: {model_config.context_window},最大输出: {model_config.max_output_tokens},工具数量: {len(agent_tools)}")

        turns = self.history_turn_parser.parse_turns(history)
        messages = [message for turn in turns for message in turn.messages]
        messages.append(current_input)
        return AgentContext(
            messages=messages,
        )