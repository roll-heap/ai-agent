from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from agent.tool import tools
from config import settings
from config import log
from exception import ErrorEnum, AgentException


# ============================================================
# 自定义 React 风格提示词（强制模型输出思考链）
# ============================================================

@dataclass
class Agent:

    @staticmethod
    def __init_llm():
        # 【1.1 加载环境变量】还可以使用 Settings 类中的方式
        # 1、默认加载项目根目录（推荐）的.env文件
        # load_dotenv()
        # 2、从当前目录向上搜索 .env
        # load_dotenv(find_dotenv())
        # 3、获取当前脚本所在目录
        # if env_path:
        #     load_dotenv(dotenv_path=env_path)
        # else:
        #     env_file = find_dotenv()
        #     if env_file:
        #         load_dotenv(dotenv_path=env_file)
        #     else:
        #         raise ValueError("未找到环境变量")


        # agent_model =
        # api_key = os.getenv("DEEPSEEK_API_KEY")
        # base_url = os.getenv("DEEPSEEK_BASE_URL")
        # if not api_key or not agent_model or not base_url:
        #     raise ValueError("环境变量缺失，请检查 .env 文件")

        # log.info(f"api_key:{api_key}")
        # ============================================================
        # 第四部分：接入大模型（DeepSeek）
        # ============================================================
        return init_chat_model(
            model=settings.model,
            model_provider="openai",    # 告诉 LangChain：请使用 OpenAI Provider 的接口协议来初始化和调用这个模型。
            api_key=settings.api_key.get_secret_value(),
            base_url=settings.base_url,
            temperature=settings.temperature,  # 0 表示输出更确定，1 表示更随机
            timeout=settings.timeout,
            max_retries=settings.max_retries,
        )


    # ============================================================
    # 第五部分：创建 Agent
    # ============================================================

    # ============================================================
    # 5. 使用 create_agent 创建 Agent（LangChain  标准方式）
    # ============================================================
    # create_agent 返回的对象本身就是可执行的，无需再包一层 AgentExecutor[reference:0]
    # system_prompt
    # 创建时，create_agent(..., system_prompt="...")设置的是Agent 初始化时设置的默认系统提示，优先级低（会被覆盖）
    # 调用时	agent.invoke({"messages": [{"role": "system", "content": "..."}]}) 实际执行 invoke 时传入的消息列表，优先级别较高（最终生效）
    @staticmethod
    def create_agent():
        try:
            react_system_prompt = Agent.get_system_prompt()
            llm = Agent.__init_llm()
            # 调试是否传入模型工具
            # print("LLM:", llm)
            # print("TOOLS:", tools)
            # bound_llm = llm.bind_tools(tools)
            # print("BOUND LLM:", bound_llm)

            # 调试模型是否调用了tool calling协议
            # result = bound_llm.invoke("查询上海现在的实时天气，必须使用 weather_tool 获取实时数据。")
            # print("========== RESULT ==========")
            # print("content:", result.content)
            # print("tool_calls:", result.tool_calls)
            # print("additional_kwargs:", result.additional_kwargs)
            # print("============================")
            return create_agent(
                model=llm,
                tools=tools,
                system_prompt=react_system_prompt,
            )
        except Exception as e:
            log.exception(f"初始化agent异常{e}")
            raise AgentException(ErrorEnum.INIT_AGENT_ERR.value)

    @staticmethod
    def get_system_prompt():
        return """你是一个智能助手。

                请根据用户的问题判断是否需要调用工具。

                如果需要工具：
                1. 选择最合适的工具。
                2. 正确填写工具参数。
                3. 根据工具返回结果回答用户。
                4. 不要编造工具没有返回的数据。
                5. 如果工具执行失败，应根据工具返回的错误信息进行回答。
                6. 如果不需要工具，可以直接回答用户。

                工具调用由系统负责执行。
                不要输出 Thought、Action、Action Input、Observation
                等传统 ReAct 中间格式。"""