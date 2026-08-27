from enum import Enum

class ErrorEnum(Enum):

    WEATHER_ERR = (1001, "查询天气异常")
    INIT_AGENT_ERR = (1002, "初始化Agent异常")
    NOT_FOUND_API_KEY = (1003, "模型缺少API-KEY")
    BASE_URL_ERR = (1004, "模型base_url配置错误")
    CAL_ERR = (1005, "计算器计算异常")
    CAL_EXPRESS_ERR = (1006, "错误：表达式中包含非法字符，请只使用数字和 + - * / ( ) . %")

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class AgentException(Exception):
    """
    python中的BaseException相当于java的Error，所以常用的是继承Exception
    """
    def __init__(self, error_code: ErrorEnum):
        self.code = error_code.code
        self.msg = error_code.msg
        super().__init__(f"{error_code.code}:{error_code.msg}")
