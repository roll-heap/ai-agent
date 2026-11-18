from abc import ABC, abstractmethod
from typing import Any, ClassVar, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

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
    def count(self,
              messages: Sequence[BaseMessage],
              model_config: ModelConfig,
              connection_config: ModelConnectionConfig,
              tool_definitions: Sequence[BaseTool] = (),
              add_generation_prompt: bool = False) -> TokenCountResult:
        """
        统计消息和工具定义的 Token 数量
        add_generation_prompt
            1、当前输入：需要按照实际生成请求添加 assistant generation prompt。
            2、历史消息：已经结束的消息序列，不需要添加生成前缀。
        """
        pass