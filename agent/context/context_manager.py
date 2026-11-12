from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from agent.context.context import AgentContext
from agent.history import HistoryTurnParser
from config import log
from exception import AgentException


class ContextManager:
    """
    1、调用 HistoryTurnParser，将原始历史解析为 ConversationTurn。
    2、根据上下文策略选择需要保留的历史轮次。
    3、必要时执行历史裁剪或压缩。
    4、将处理后的历史与当前输入组装成 AgentContext。
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