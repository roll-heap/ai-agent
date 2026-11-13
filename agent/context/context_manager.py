from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from agent.context.context import AgentContext
from agent.history import HistoryTurnParser
from config import log
from exception import AgentException


class ContextManager:
    """
        1、接收构建上下文所需的数据
            Conversation 将当前请求的原始历史、当前输入、任务分类结果和模型配置传给 ContextManager。
        2、解析历史轮次
            调用现有的 HistoryTurnParser.parse_turns(history)，得到 ConversationTurn 列表。
        3、计算固定输入开销
            使用共享的 TokenCounter 计算系统提示词、工具定义、当前输入等所需 Token。
        4、估算输出 Token 预算
            调用 OutputTokenBudgetEstimator，根据 TaskType 选择策略，得到本轮输出预算。
        5、计算历史可用预算
            从模型上下文窗口中扣除固定开销、当前输入、输出预留和安全余量，得到历史可用预算。
        6、选择近期原始历史
            调用 HistorySelector，按照 Fixed Turn Window 或 Token Budget 策略选择完整轮次。
        7、处理历史摘要
            调用 SummaryManager，判断摘要是否有效，是否需要复用、增量更新或完整重建。
        8、最终预算校验与上下文组装
            组合系统提示词、摘要、近期原始历史和当前输入，验证 Token 总量，生成 AgentContext。
    """
    def __init__(self, history_turn_parser: HistoryTurnParser):
        self.history_turn_parser = history_turn_parser

    def build_context(self, history: Sequence[BaseMessage], current_input: BaseMessage) -> AgentContext:
        """
        解析历史消息，并组装本轮 Agent 执行上下文。
        """
        log.info(f"session.history:{history}")
        # 当前阶段只接受 HumanMessage，其他消息类型直接报错。
        if not isinstance(current_input, HumanMessage):
            raise AgentException("当前阶段只接受HumanMessage")

        turns = self.history_turn_parser.parse_turns(history)
        messages = [message for turn in turns for message in turn.messages]
        messages.append(current_input)
        return AgentContext(messages=messages)