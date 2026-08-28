import math


class CalculaterDao:
    @staticmethod
    def calculater(expression: str) -> str:
        result = eval(
            expression,
            {"__builtins__": {}},  # 禁止所有内置函数
            {}
        )
        return f"{expression} = {result}"
