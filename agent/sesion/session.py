from dataclasses import dataclass, field
from uuid import uuid4

from langchain_core.messages import BaseMessage


@dataclass
class Session:
    """
    负责保存一次会话的历史消息
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    history: list[BaseMessage] = field(default_factory=list)