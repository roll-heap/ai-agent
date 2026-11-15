from agent.model import ModelConnectionConfig, ModelConfig
from agent.profile.agent_profile_registry import AgentProfile
from agent.profile.agent_profile_registry import AgentProfileRegistry
from agent.tool.tool import tools_dict
from config.settings import Setting
from exception import AgentException


class ProfileFactory:
    """
    AgentProfile组装工厂
    负责创建不同用途的AgentProfile
    不负责创建和缓存Agent
    """
    def __init__(self,settings: Setting):
        self.settings = settings

    def _get_model_configs(self, model_key: str) -> tuple[ModelConfig, ModelConnectionConfig]:
        model_settings = self.settings.models.get(model_key)
        if model_settings is None:
            raise AgentException(f"模型配置不存在：{model_key}")
        model_config = ModelConfig(
            model_name=model_settings.model_name,
            context_window=model_settings.context_window,
            max_output_tokens=model_settings.max_output_tokens
        )
        model_connection_config = ModelConnectionConfig(
            model_provider=model_settings.model_provider,
            api_key=model_settings.api_key,
            base_url=model_settings.base_url,
            temperature=model_settings.temperature,
            timeout=model_settings.timeout,
            max_retries=model_settings.max_retries
        )
        return model_config, model_connection_config

    @staticmethod
    def _get_tools(tool_names: list[str]) -> tuple:
        tools_result = []
        for name in tool_names:
            tool = tools_dict.get(name.strip())
            if tool is None:
                raise AgentException(f"工具不存在：{name}")
            tools_result.append(tool)
        return tuple(tools_result)

    def create_registry(self) -> AgentProfileRegistry:
        profiles = []
        for profile_name, model_key in self.settings.agent_model_map.items():
            agent_profile = self.settings.agent_profile.get(profile_name)
            if agent_profile is None:
                raise AgentException(f"Agent Profile配置不存在：{profile_name}")
            tool_names = agent_profile.tools
            tools = ProfileFactory._get_tools(tool_names)
            model_config, connection_config = self._get_model_configs(model_key)
            profiles.append(AgentProfile(
                name=profile_name,
                description=agent_profile.description,
                model_config=model_config,
                connection_config=connection_config,
                system_prompt=agent_profile.system_prompt,
                tools=tools
            ))
        return AgentProfileRegistry(profiles=profiles)
