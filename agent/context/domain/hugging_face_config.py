from dataclasses import dataclass


@dataclass(frozen=True)
class HuggingFaceConfig:
    """Hugging Face Tokenizer配置"""
    name_or_path: str
    revision: str | None = None
    chat_template: str | None = None
    # 只有确认Tokenizer,chat Template和工具格式与实际模型服务的输入处理方式一致时，才设置为True
    runtime_compatible: bool = False