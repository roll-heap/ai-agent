import re

from agent.tool.dao import CalculaterDao
from agent.tool.domain import ToolResponseModel
from exception import ErrorEnum


class CalculaterService:
    @staticmethod
    def calculater(expression: str) -> ToolResponseModel:
        """
            执行数学计算，支持加减乘除、幂运算、括号。
            参数:
                expression: 数学表达式，例如 "3 + 5 * 2" 或 "(8 + 2) * 3"
        """
        # 1. 安全检查：只允许数字、运算符、括号、小数点、空格
        allowed_pattern = r'^[\d+\-*/().%\s]+$'
        if not re.match(allowed_pattern, expression):
            return ToolResponseModel(success=False, msg=ErrorEnum.CAL_EXPRESS_ERR.value)
        try:
            result = CalculaterDao.calculater(expression)
            return ToolResponseModel(data=result)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))
