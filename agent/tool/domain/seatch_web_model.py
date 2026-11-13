from pydantic import BaseModel, Field


class SearchWebModel(BaseModel):
    title: str = Field(description="标题")
    href: str = Field(description="链接")
    body: str = Field(description="内容")