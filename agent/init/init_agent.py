from dataclasses import dataclass

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agent.tool.tool import tools
from config.config import settings
from config.logger_core import log
from exception.agent_exception import ErrorEnum, AgentException


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
        return ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key.get_secret_value(),
            base_url=settings.base_url,
            temperature=settings.temperature,  # 0 表示输出更确定，1 表示更随机
            timeout=settings.timeout,
            max_retries=settings.max_retries,
            streaming=True,
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
            return create_agent(
                model=llm,
                tools=tools,
                system_prompt=react_system_prompt,
            )
        except Exception as e:
            log.exception(f"初始化agent异常{e}")
            raise AgentException(ErrorEnum.INIT_AGENT_ERR)

    @staticmethod
    def get_system_prompt():
        return """你是一个智能助手。

                你可以使用提供的工具来完成用户任务。

                工具使用规则：
                1. 需要实时数据时，必须调用对应工具，不能自己编造数据。
                2. 计算数学表达式时，优先使用计算器工具。
                3. 查询天气时，使用天气工具。
                4. 查询当前时间时，使用当前时间工具。
                5. 需要读取网页时，使用网页抓取工具。
                6. 需要读取文件时，使用文件读取工具。
                7. 需要写入文件时，使用文件写入工具。
                8. 工具返回结果后，根据工具结果回答用户。
                9. 不要向用户暴露内部推理过程。"""

# 帮助用户查询任意城市的实时天气信息，计算数学运算，获取最新时间"""