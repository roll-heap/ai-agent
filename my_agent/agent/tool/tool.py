from langchain.tools import tool
from my_agent.agent.biz.weather import Weather


@tool
def weather_tool(city) -> str:
    """
    查询某个城市的天气。
    :param city:
    :return:
    """
    return Weather.query(city)