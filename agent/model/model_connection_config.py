from dataclasses import dataclass

from pydantic import SecretStr


@dataclass
class ModelConnectionConfig:
    """模型连接与调用配置"""
    model_provider: str
    api_key: SecretStr
    base_url: str
    temperature: float = 0
    timeout: int = 30
    max_retries: int = 2