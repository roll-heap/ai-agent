from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型能力与限制配置"""
    # 模型名字
    model_name: str
    # 模型桑下文窗口大小
    context_window: int
    # 模型最大输出Token数
    max_output_tokens: int