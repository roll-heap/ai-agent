from dataclasses import dataclass
from typing import Sequence, Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from agent.model import ModelConnectionConfig, ModelConfig
from config import log
from exception import ErrorEnum, AgentException


@dataclass
class Agent:

    @staticmethod
    def _init_llm(model_config: ModelConfig, connection_config: ModelConnectionConfig):
        """根据模型连接配置初始化 LangChain ChatModel。"""
        return init_chat_model(
            model=model_config.model_name,
            model_provider=connection_config.model_provider,    # 告诉 LangChain：请使用 OpenAI Provider 的接口协议来初始化和调用这个模型。
            api_key=connection_config.api_key.get_secret_value(),
            base_url=connection_config.base_url,
            temperature=connection_config.temperature,  # 0 表示输出更确定，1 表示更随机
            timeout=connection_config.timeout,
            max_retries=connection_config.max_retries,
        )

    @staticmethod
    def create_agent(model_config: ModelConfig, connection_config: ModelConnectionConfig, system_prompt: str|None = None,
                     agent_tools: Sequence[BaseTool] | None = None,):
        """根据运行配置创建 LangChain Agent。"""
        try:
            model = Agent._init_llm(model_config=model_config, connection_config=connection_config)
            return create_agent(model=model,tools=agent_tools,system_prompt=system_prompt)
        except Exception as e:
            log.exception(f"初始化agent异常{e}")
            raise AgentException(ErrorEnum.INIT_AGENT_ERR.value)

    # @staticmethod
    # def get_system_prompt():
    #     return """你是一个智能助手。
    #             请根据用户的问题判断是否需要调用工具。
    #             如果需要工具：
    #             1. 选择最合适的工具。
    #             2. 正确填写工具参数。
    #             3. 根据工具返回结果回答用户。
    #             4. 不要编造工具没有返回的数据。
    #             5. 如果工具执行失败，应根据工具返回的错误信息进行回答。
    #             6. 如果不需要工具，可以直接回答用户。
    #             工具调用由系统负责执行。
    #             不要输出 Thought、Action、Action Input、Observation
    #             等传统 ReAct 中间格式。"""