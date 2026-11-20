from dataclasses import dataclass, field
from uuid import uuid4

from langchain_core.messages import BaseMessage

from agent.context.domain import SummeryState


@dataclass
class Session:
    """
    保存完整会话数据，不因某一轮上下文筛选而丢失原始历史。
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    history: list[BaseMessage] = field(default_factory=list)
    # default_factory 很重要：每个 Session 都必须拥有独立的 SummaryState，不能让多个会话共享同一个实例
    summary_state: SummeryState=field(default_factory=SummeryState)