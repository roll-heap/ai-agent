from dataclasses import dataclass

from langchain_core.messages import BaseMessage


@dataclass
class ConversationTurn:
    """一轮对话及其完整性状态"""
    messages: list[BaseMessage]
    is_complete: bool