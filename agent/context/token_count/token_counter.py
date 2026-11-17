from typing import Sequence, Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage

from agent.context.domain import TokenCountResult, TokenCountAccuracy


class TokenCounter:
    """基于langChain模型接口统计完整消息的Token数量"""
    @staticmethod
    def count_messages(
            messages: list[BaseMessage],
            model: BaseLanguageModel,
            tools: Sequence[Any] | None = None
    ) -> TokenCountResult:
        """统计完整消息列表的token数量"""
        tokens = model.get_num_tokens_from_messages(
            messages=messages,
            tools=tools
        )
        if tokens < 0:
            raise ValueError(f"token数量不能小于0")
        return TokenCountResult(total_tokens=tokens, accuracy=TokenCountAccuracy.ESTIMATED)