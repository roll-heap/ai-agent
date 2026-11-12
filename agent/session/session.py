from dataclasses import dataclass, field
from uuid import uuid4

from langchain_core.messages import BaseMessage


@dataclass
class Session:
    """
    保存完整会话数据，不因某一轮上下文筛选而丢失原始历史。
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    history: list[BaseMessage] = field(default_factory=list)