from typing import Any

from agent.context.domain import InputModality, TokenCountAccuracy
from agent.model import ModelConfig
from common.demo.strategies.base_token_count_strategy import BaseTokenCountStrategy


class TokenizerFactory:
    pass


class TextStrategy(BaseTokenCountStrategy):
    """
    文本Token计算策略
    """
    modality = InputModality.TEXT

    def count(self, content: Any, model_config: ModelConfig) -> tuple[int, TokenCountAccuracy]:
        if not isinstance(content, str):
            content = str(content)
        tokenizer = TokenizerFactory.get_tokenizer(model_config)
        tokens = tokenizer.encode(content)
        return len(tokens), TokenCountAccuracy.ESTIMATED