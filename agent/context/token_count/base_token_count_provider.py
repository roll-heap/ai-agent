from abc import ABC, abstractmethod
from typing import Any, ClassVar, Sequence

from langchain_core.messages import BaseMessage

from agent.context.domain import TokenCountResult
from agent.model import ModelConfig, ModelConnectionConfig


class BaseTokenCountProvider(ABC):
    """Token 统计 Provider 基类"""

    provider_name: ClassVar[str]
    priority: ClassVar[int] = 0

    @abstractmethod
    def supports(self,model_config: ModelConfig,connection_config: ModelConnectionConfig) -> bool:
        """判断当前 Provider 是否支持指定模型"""
        pass

    @abstractmethod
    def count(self,messages: Sequence[BaseMessage],tools: Sequence[Any] | None = None) -> TokenCountResult:
        """统计消息和工具定义的 Token 数量"""
        pass