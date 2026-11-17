from dataclasses import dataclass
from typing import Any, Sequence

from langchain_core.language_models import BaseChatModel

from agent.model import ModelConfig, ModelConnectionConfig


@dataclass(frozen=True)
class AgentRuntimeConfig:
    """
    单词请求使用的完整agent运行配置
    这四个字段必须来自同一次 Agent 创建所使用的配置，不能分别从不同地方获取
    """
    # 本轮实际执行的 LangChain Agent
    agent: Any
    # 当前模型的上下文窗口和输出限制
    model_config: ModelConfig
    connection_config: ModelConnectionConfig
    # 本轮实际使用的系统提示词
    system_prompt: str
    # 本轮实际提供给 Agent 的工具
    tools: Sequence[Any]