from enum import Enum

class ErrorEnum(Enum):
    SUCCESS = "成功"
    WEATHER_ERR = "查询天气异常"
    INIT_AGENT_ERR = "初始化Agent异常"
    NOT_FOUND_API_KEY = "模型缺少API-KEY"
    BASE_URL_ERR = "模型base_url配置错误"
    CAL_ERR = "计算器计算异常"
    CAL_EXPRESS_ERR = "错误：表达式中包含非法字符，请只使用数字和 + - * / ( ) . %"

    def __init__(self, msg):
        self.msg = msg


class AgentException(Exception):
    """
    python中的BaseException相当于java的Error，所以常用的是继承Exception
    """
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)
