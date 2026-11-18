from dataclasses import dataclass


@dataclass(frozen=True)
class HuggingFaceConfig:
    """Hugging Face Tokenizer配置"""
    # Hugging Face Tokenizer 的模型名称或本地路径
    name_or_path: str
    # Tokenizer 版本
    revision: str | None = None
    # 指定使用的 Chat Template
    chat_template: str | None = None
    # 是否已经验证与实际模型服务输入格式兼容
    runtime_compatible: bool = False