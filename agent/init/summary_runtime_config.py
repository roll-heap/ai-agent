from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from agent.model import ModelConfig, ModelConnectionConfig


@dataclass(frozen=True)
class SummaryRuntimeConfig:
    """
    摘要模型运行配置
    """
    # 独立摘要模型实例,所有符合 LangChain ChatModel 接口的聊天模型的共同类型
    model:BaseChatModel
    # 摘要模型能力与限制配置
    model_config: ModelConfig
    # 摘要模型连接配置
    connection_config:ModelConnectionConfig