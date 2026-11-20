from dataclasses import dataclass


@dataclass(frozen=True)
class ContextBudgetConfig:
    """上下文预算配置 这里的默认值是建议初始值，后续可以通过配置调整"""
    # 默认输出token预算
    # default_output_tokens: int
    # 基础安全余量
    safety_base_tokens: int
    # 估算Token误差补偿比例
    safety_ratio: float


