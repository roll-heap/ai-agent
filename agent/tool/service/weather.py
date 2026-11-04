from agent.tool.dao import WeatherDao
from agent.tool.model import ToolResponseModel
from exception import AgentException


# ============================================================
# 1. 实体类（Weather）
# ============================================================
class WeatherService:
    @staticmethod
    def query_weather(city: str) -> ToolResponseModel:
        try:
            data = WeatherDao.query_weather(city)
            return ToolResponseModel(data=data)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))