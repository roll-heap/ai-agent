from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from agent.context.context import AgentContext
from agent.context.token_count import TokenCounter
from agent.history import HistoryTurnParser
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
    ):
        self.history_turn_parser = history_turn_parser
        self.token_counter = token_counter

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
        # 3、组装历史消息和当前输入
        history_messages = [message for turn in complete_turns for message in turn.messages]
        agent_messages = [
            *history_messages,
            current_input
        ]
        token_message = [
            SystemMessage(content=runtime_config.system_prompt),
            *agent_messages,
        ]
        # 4、组装用于 Token 统计的完整消息
        current_token_result = self.token_counter.count(
            messages=token_message,
            model_config=model_config,
            connection_config=connection_config,
            tool_definitions=runtime_config.tools,
            add_generation_prompt=True
        )
        # 5、获取本次请求的输出预留预算
        output_token_budge = model_config.max_output_tokens
        log.info(f"固定输入Token:{current_token_result.total_tokens}，统计精度：{current_token_result.accuracy.value}"
                 f"统计完整性：{current_token_result.completeness.value},输出预留预算：{output_token_budge}"
                 f"完整历史轮次：{len(complete_turns)}, 排除不完整轮次：{len(turns) - len(complete_turns)}")
        # 暂时保留完整历史和当前输入，后续步骤再进行历史预算筛选

        return AgentContext(messages=agent_messages)