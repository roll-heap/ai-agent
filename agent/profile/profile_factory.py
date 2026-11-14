from agent.model import ModelConnectionConfig, ModelConfig
from agent.profile import AgentProfileRegistry, AgentProfile
from agent.tool.tool import weather_tool, calculate_tool, current_time_tool, fetch_webpage_tool, read_file_tool, \
    write_file_tool, list_directory_tool, read_file_metadata_tool, system_info_tool, system_resource_tool, \
    search_web_tool


class ProfileFactory:
    """
    AgentProfile组装工厂
    负责创建不同用途的AgentProfile
    不负责创建和缓存Agent
    """
    def __init__(
            self,
            model_config: ModelConfig,
            connection_config: ModelConnectionConfig
    ):
        self.model_config = model_config
        self.connection_config = connection_config

    def create_registry(self) -> AgentProfileRegistry:
        # 通用助手：使用全部工具
        assistant_tools = (
            weather_tool,
            calculate_tool,
            current_time_tool,
            fetch_webpage_tool,
            read_file_tool,
            write_file_tool,
            list_directory_tool,
            read_file_metadata_tool,
            system_info_tool,
            system_resource_tool,
            search_web_tool
        )

        # 编程助手：文件操作和计算工具
        coder_tools = (
            calculate_tool,
            read_file_tool,
            write_file_tool,
            list_directory_tool,
            read_file_metadata_tool,
        )

        # 研究助手：搜索、网页读取和时间工具
        researcher_tools = (
            search_web_tool,
            fetch_webpage_tool,
            current_time_tool,
        )

        profiles = (
            AgentProfile(
                name="assistant",
                description="通用智能助手",
                model_config=self.model_config,
                connection_config=self.connection_config,
                system_prompt="你是一个通用智能助手，负责理解用户需求并提供准确、有帮组的回答。",
                tools=assistant_tools
            ),
            AgentProfile(
                name="coder",
                description="编程开发助手",
                model_config=self.model_config,
                connection_config=self.connection_config,
                system_prompt="你是一个专业的编程助手，擅长代码分析、编写、修改和调试。",
                tools=coder_tools,
            ),
            AgentProfile(
                name="researcher",
                description="资料研究助手",
                model_config=self.model_config,
                connection_config=self.connection_config,
                system_prompt="你是一个研究助手，擅长搜索资料、阅读网页和整理信息。",
                tools=researcher_tools,
            ),
        )

        return AgentProfileRegistry(profiles=profiles)
