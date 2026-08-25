from enum import Enum


class ErrorCode(Enum):
    WEATHER_ERROR = ("1001", "查询天气异常")
    CREATE_AGENT_ERR = ("1002", "创建agent异常")
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
