import math


class CalculaterDao:
    @staticmethod
    def calculater(expression: str) -> str:
        result = eval(
            expression,
            {"__builtins__": {}},  # 禁止所有内置函数
            {"math": math}  # 只允许 math 模块
        )
        return f"{expression} = {result}"
