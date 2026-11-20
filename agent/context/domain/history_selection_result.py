from dataclasses import dataclass

from langchain_core.messages import BaseMessage

from agent.context.domain import TokenCountResult
from agent.history import ConversationTurn


@dataclass
class HistorySelectionResult:
    """历史轮次筛选结果"""
    # 最终交给Agent的消息
    messages:list[BaseMessage]
    # 本次保留的完整历史轮次
    retained_turns:list[ConversationTurn]
    # 本次因预算不足而裁剪的完整历史轮次
    excluded_turns:list[ConversationTurn]
    # 最终完整上下文的Token统计结果
    token_result:TokenCountResult