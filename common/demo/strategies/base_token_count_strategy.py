from abc import ABC, abstractmethod
from typing import Any, ClassVar

from agent.context.domain import InputModality
from agent.model import ModelConfig
from agent.context.domain.token_count_result import TokenCountAccuracy


class BaseTokenCountStrategy(ABC):
    """
    token计算策略基类
    """

    modality: ClassVar[InputModality]


    @abstractmethod
    def count(self, content: Any, model_config: ModelConfig) -> tuple[int ,TokenCountAccuracy]:
        """
        计算当前内容的token数量
        Args:
            content:当前模态的内容
            model_config:模型配置
        Returns:
            (token数量， 计算精度)
        """
        raise NotImplementedError