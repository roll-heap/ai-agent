import logging
import re
from dataclasses import dataclass
from datetime import datetime

import requests

from exception.agent_exception import ErrorEnum, AgentException


# ============================================================
# 1. 实体类（Weather）
# ============================================================
@dataclass
class Weather:
    city: str
    weather: str
    temperature: str
    wind: str
    query_time: str

    @classmethod
    def api_weather(cls, city: str) -> "Weather":
        url = f"https://wttr.in/{city}?format=%C+%t+%w"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        raw_text = response.text
        # print(f"API返回的数据：{raw_text}")
        # 用正则提取关键信息
        # 示例返回： "Sunny +25°C 15 km/h"
        # raw = raw_text.split(" ")
        weather_match = re.search(r'^([A-Za-z\s]+)', raw_text)  # 取开头的非数字部分（天气状况）
        temp_match = re.search(r'([+-]?\d+)°C', raw_text)  # 取温度数字
        wind_match = re.search(r'(\d+)\s*km/h', raw_text)  # 取风速数字
        weather = weather_match.group(1).strip() if weather_match else "未知"
        temp = temp_match.group(1).strip() if temp_match else "N/A"
        wind = wind_match.group(1).strip() if wind_match else "N/A"

        # 5. 输出结构化结果
        return cls(city, weather, temp, wind, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    # ============================================================
    # 2. 业务函数（供 Agent 调用）
    # ============================================================
    @staticmethod
    def query_weather(city_name: str):
        try:
            data = Weather.api_weather(city_name)
            return (
                f"城市：{data.city}\n"
                f"天气：{data.weather}\n"
                f"温度：{data.temperature}°C\n"
                f"风速：{data.wind} km/h\n"
                f"查询时间：{data.query_time}"
            )
        except Exception as e:
            logging.exception(f"查询天气失败,{e}")
            raise AgentException(ErrorEnum.WEATHER_ERR)




