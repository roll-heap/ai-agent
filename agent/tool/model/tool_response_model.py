from typing import Any

from pydantic import BaseModel, Field

from exception.agent_exception import ErrorEnum


class ToolResponseModel(BaseModel):
    """
       所有 Tool 的统一返回模型
       """
    success: bool = Field(default=True, description="工具执行是否成功")
    data: Any = Field(default=None, description="工具执行返回的数据")
    msg: str = Field(default=ErrorEnum.SUCCESS.value, description="工具执行结果说明")

