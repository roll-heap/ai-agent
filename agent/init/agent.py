import logging

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agent.tool.tool import weather_tool
from config.env_config import config
from exception.AgentException import AgentException
from exception.error_code import ErrorCode


class Agent:
    @staticmethod
    def __init_llm__():
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            temperature=config.temperature,
            max_retries=config.max_retries,
            timeout=config.timeout
        )

    @staticmethod
    def create_agent():
        try:
            llm = Agent.__init_llm__()
            return create_agent(
                model=llm,
                tools=[weather_tool],
                system_prompt="你是一个智能天气助手，可以帮助用户查询任意城市的实时天气信息。"
            )
        except Exception as e:
            logging.exception(e)
            raise AgentException(ErrorCode.CREATE_AGENT_ERR)
