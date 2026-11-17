# 这样所有注解都自动变成字符串，延迟到需要时再解析。于是不用手动加引号了，针对merge方法
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from agent.model.domain import InputModality
from exception import AgentException


class TokenCountAccuracy(str, Enum):
    """Token 计算精度。"""
    # 精确
    EXACT = "exact"
    # 估值
    ESTIMATED = "estimated"


@dataclass
class ModalityTokenCount:
    """单种模态的 Token 统计。"""
    modality: InputModality
    tokens: int
    accuracy: TokenCountAccuracy


@dataclass
class TokenCountResult:
    """Token 统计结果。"""
    total_tokens: int = 0
    modality_counts: dict[InputModality, ModalityTokenCount] = field(default_factory=dict)
    accuracy: TokenCountAccuracy = TokenCountAccuracy.EXACT

    def add(self, modality: InputModality, tokens:int, accuracy: TokenCountAccuracy) -> None:
        """添加某种模态的token数量"""
        if tokens < 0:
            raise AgentException("token数量不能小于0")
        self.total_tokens += tokens
        if modality not in self.modality_counts:
            self.modality_counts[modality] = ModalityTokenCount(modality, tokens, accuracy)
        else:
            item = self.modality_counts[modality]
            item.tokens += tokens
            if accuracy == TokenCountAccuracy.ESTIMATED:
                item.accuracy = TokenCountAccuracy.ESTIMATED
        if accuracy == TokenCountAccuracy.ESTIMATED:
            self.accuracy = TokenCountAccuracy.ESTIMATED

    def merge(self, other: TokenCountResult) -> None:
        """合并另一个统计结果"""
        for modality, item in other.modality_counts.items():
            self.add(modality=modality, tokens=item.tokens, accuracy=item.accuracy)