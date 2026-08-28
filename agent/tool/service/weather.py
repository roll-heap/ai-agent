from dataclasses import dataclass

from agent.tool.dao.weather_dao import WeatherDao
from agent.tool.model.weater_model import WeatherModel


# ============================================================
# 1. 实体类（Weather）
# ============================================================
@dataclass
class WeatherService:
    @staticmethod
    def query_weather(city: str) -> dict:
        try:
            data = WeatherDao.query_weather(city)
            return {
                "success": True,
                "data": data.model_dump(mode="json")
            }
        except Exception as e:
            return {
                "success": False,
                "data": str(e)
            }
