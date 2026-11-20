from dataclasses import dataclass, field
from typing import Sequence
from uuid import uuid4

from langchain_core.messages import BaseMessage

from agent.context.domain import SummaryState


@dataclass
class Session:
    """
    保存完整会话数据，不因某一轮上下文筛选而丢失原始历史。
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    history: list[BaseMessage] = field(default_factory=list)
    # default_factory 很重要：每个 Session 都必须拥有独立的 SummaryState，不能让多个会话共享同一个实例
    summary_state: SummaryState=field(default_factory=SummaryState)

    def append_messages(self, messages: Sequence[BaseMessage]) -> None:
        """
        向回话历史追加消息
        只允许追加，不负责删除、裁剪或重排历史
        """
        if not messages:
            return
        self.history.extend(messages)