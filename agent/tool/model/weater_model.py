from pydantic import BaseModel, Field


class WeatherModel(BaseModel):
    city: str = Field(description="城市")
    weather: str = Field(description="天气")
    temperature: str = Field(description="温度")
    wind: str = Field(description="风速，单位：km/h")
    query_time: str = Field(description="天气查询时间")
