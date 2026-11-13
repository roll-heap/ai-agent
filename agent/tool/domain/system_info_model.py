
from pydantic import BaseModel, Field


class SystemInfoModel(BaseModel):
    os_name: str = Field(description="操作系统")
    os_version: str = Field(description="系统版本")
    architecture: str = Field(description="系统架构")
    hostname: str = Field(description="当前主机名称")
    python_version: str = Field(description="python版本")
    current_work_directory: str = Field(description="当前工作目录")