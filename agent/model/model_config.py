from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型能力与限制配置"""
    # 模型名字
    model_name: str
    # 模型上下文窗口大小
    context_window: int
    # 模型最大输出 Token 数
    max_output_tokens: int
    # Tokenizer 名称或 Hugging Face 模型路径
    tokenizer_name: str | None = None