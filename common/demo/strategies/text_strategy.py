from typing import Any

from agent.model import ModelConfig
from agent.model.domain import TokenCountAccuracy, InputModality
from common.demo.strategies.base_token_count_strategy import BaseTokenCountStrategy
from agent.model.token_counter.tokenizer_factory import TokenizerFactory


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