from dataclasses import dataclass

from agent.context.token_count import TokenCountResult


@dataclass
class TokenBudgetResult:
    """token预算计算结果"""
    # 固定输入token统计结果
    input_token_count: TokenCountResult
    # 本轮输出token预算

