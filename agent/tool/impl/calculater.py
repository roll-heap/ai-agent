import math
import re

from exception.agent_exception import ErrorEnum, AgentException


def calculater(expression: str):
    """
        执行数学计算，支持加减乘除、幂运算、括号。
        参数:
            expression: 数学表达式，例如 "3 + 5 * 2" 或 "(8 + 2) * 3"
    """
    # 1. 安全检查：只允许数字、运算符、括号、小数点、空格
    allowed_pattern = r'^[\d+\-*/().%\s]+$'
    if not re.match(allowed_pattern, expression):
        raise AgentException(ErrorEnum.CAL_EXPRESS_ERR)
    try:
        result = eval(
            expression,
            {"__builtins__":{}},    # 禁止所有内置函数
            {"math": math}          # 只允许 math 模块
        )
        return f"{expression} = {result}"
    except Exception as e:
        raise AgentException(ErrorEnum.CAL_ERR)
