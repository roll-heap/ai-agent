from typing import Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from agent.context.domain import TokenCountResult
from agent.context.token_count import provider
from agent.context.token_count.provider.base_token_count_provider import BaseTokenCountProvider
from agent.model import ModelConfig, ModelConnectionConfig
from common import Registry
from exception import AgentException


class TokenCounter:
    """基于langChain模型接口统计完整消息的Token数量"""

    def __init__(self):
        self.registry = Registry[str, BaseTokenCountProvider](
            base_class=BaseTokenCountProvider,
            package=provider,
            key_getter=lambda cls: cls.provider_name,
        )

    def _get_provider(self,model_config: ModelConfig, connection_config: ModelConnectionConfig) -> BaseTokenCountProvider:
        """选择适配当前模型的token统计Provider"""
        providers = [provide for provide in self.registry.items.values()
                     if provide.supports(model_config, connection_config)]
        if not providers:
            raise AgentException(f"没有找到适配模型的 Token 统计 Provider：{connection_config.model_provider} {model_config.model_name}")
        providers.sort(key=lambda provide: provide.priority, reverse=True)
        return providers[0]

    def count(
            self,
            messages: list[BaseMessage],
            model_config: ModelConfig,
            connection_config: ModelConnectionConfig,
            tool_definitions: Sequence[BaseTool]=(),
            add_generation_prompt:bool=False
    ) -> TokenCountResult:
        """统计完整消息列表的token数量"""
        provide = self._get_provider(model_config=model_config, connection_config=connection_config)
        return provide.count(
            messages=messages,
            model_config=model_config,
            connection_config=connection_config,
            tool_definitions=tool_definitions,
            add_generation_prompt=add_generation_prompt
        )