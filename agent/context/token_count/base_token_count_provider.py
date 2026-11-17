from abc import ABC, abstractmethod
from typing import Sequence, Any

from langchain_core.messages import BaseMessage

from agent.context.domain import TokenCountResult


class BaseTokenCountProvider(ABC):
    """Token 统计 Provider 抽象接口"""

    @abstractmethod
    def count(self, message: Sequence[BaseMessage], tools: Sequence[Any] | None = None) -> TokenCountResult:
        """统计消息和工具定义的 Token 数量"""
        pass