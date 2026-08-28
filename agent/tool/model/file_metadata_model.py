from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass
class FileMetaDataModel(BaseModel):
    """文件元数据"""
    name:str = Field(description="文件名")
    path: str = Field(description="文件路径")
    suffix: str = Field(description="文件后缀")
    size: int = Field(description="文件大小")

    created_time: datetime = Field(description="文件创建时间")
    modified_time: datetime = Field(description="文件修改时间")
