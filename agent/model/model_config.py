from dataclasses import dataclass

from agent.context.domain import HuggingFaceConfig


@dataclass
class ModelConfig:
    """模型能力与限制配置"""
    # 模型名字
    model_name: str
    # 模型上下文窗口大小
    context_window: int
    # 模型最大输出 Token 数
    max_output_tokens: int
    hugging_face_config: HuggingFaceConfig | None = None