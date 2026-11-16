import json
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence, Any

import math
from langchain_core.messages import BaseMessage

from exception import AgentException


class TokenCountAccuracy(Enum):
    """token 计数精度"""
    # 精确
    EXACT = "exact"
    # 估值
    ESTIMATED = "estimated"
    # 保守
    CONSERVATIVE = "conservative"

@dataclass(frozen=True)
class TokenCountResult:
    """Token 技术结果(计数结果是一次计算产生的值，不需要在后续流程中修改。所以frozen=True)"""
    token_count: int
    # 准确度
    accuracy: TokenCountAccuracy

class TokenCounter:
    """
    token计数器
    负责统计文本、消息和工具定义的Token数量
    不负责上下预算分配和历史筛选
    """
    def __init__(self, tokenizer: Callable[[str], int] | None = None, chars_per_token: float = 4.0):
        if chars_per_token <= 0:
            raise AgentException("chars_per_token必须大于0")
        self.tokenizer = tokenizer
        self.chars_per_token = chars_per_token

    def _count(self, text: str) -> TokenCountResult:
        """统一计数入口"""
        if not text:
            return TokenCountResult(
                token_count=0,
                accuracy=TokenCountAccuracy.EXACT if self.tokenizer is not None else TokenCountAccuracy.ESTIMATED
            )
        if self.tokenizer is not None:
            return TokenCountResult(token_count=self.tokenizer(text), accuracy=TokenCountAccuracy.EXACT)
        token_count = math.ceil(len(text) / self.chars_per_token)
        return TokenCountResult(token_count=token_count,accuracy=TokenCountAccuracy.ESTIMATED)

    def count_text(self, text: str) -> TokenCountResult:
        """
        统计普通文本的Token数量
        count_text() 可以标记为 EXACT，但消息和工具仍然标记为 ESTIMATED。因为模型服务商可能对消息和工具定义进行额外封装，Tokenizer 本身无法覆盖这些开销。
        """
        return self._count(text)

    def count_messages(self, messages: Sequence[BaseMessage]) -> TokenCountResult:
        """统计消息序列的Token数量"""
        message_data = [message.model_dump(mode="json", exclude_none=True) for message in messages]
        text = json.dumps(message_data, ensure_ascii=False, default=str)
        result = self._count(text)
        # 消息序列还设计模型服务商的消息封装开销，即使使用 Tokenizer，也不代表真是请求Token完全精确
        return TokenCountResult(token_count=result.token_count, accuracy=TokenCountAccuracy.ESTIMATED)

    def count_tools(self, tools: Sequence[Any]) -> TokenCountResult:
        """统计工具定义的Token数量"""
        tool_definitions = []
        for tool in tools:
            schema = getattr(tool, "args_schema", None)
            if schema is not None and hasattr(schema, "model_json_schema"):
                schema = schema.model_json_schema()
            tool_definitions.append({
                "name": getattr(tool, "name", ""),
                "description": getattr(tool, "description", ""),
                "parameters": schema,
            })
        text = json.dumps(tool_definitions, ensure_ascii=False, default=str)
        result = self._count(text)
        # 工具定义在实际模型请求中还可能经过服务商转换
        return TokenCountResult(token_count=result.token_count, accuracy=TokenCountAccuracy.ESTIMATED)