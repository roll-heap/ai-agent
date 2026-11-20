# 这样所有注解都自动变成字符串，延迟到需要时再解析。于是不用手动加引号了，针对merge方法
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from exception import AgentException


class TokenCountAccuracy(str, Enum):
    """Token 计算精度。"""
    # 精确
    EXACT = "exact"
    # 估值
    ESTIMATED = "estimated"

class TokenCountCompleteness(str, Enum):
    """Token 统计完整性"""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

@dataclass
class TokenCountResult:
    """Token 统计结果。"""
    total_tokens: int = 0
    accuracy: TokenCountAccuracy = TokenCountAccuracy.EXACT
    completeness: TokenCountCompleteness = TokenCountCompleteness.COMPLETE

    def add(self, tokens: int, accuracy: TokenCountAccuracy, completeness: TokenCountCompleteness) -> None:
        """累加 Token 数量"""
        if tokens < 0:
            raise AgentException("token数量不能小于0")
        self.total_tokens += tokens
        if accuracy == TokenCountAccuracy.ESTIMATED:
            self.accuracy = TokenCountAccuracy.ESTIMATED
        if completeness == TokenCountCompleteness.INCOMPLETE:
            self.completeness = TokenCountCompleteness.INCOMPLETE

    def merge(self, other: TokenCountResult) -> None:
        """合并另一个统计结果"""
        self.add(tokens=other.total_tokens, accuracy=other.accuracy, completeness=other.completeness)