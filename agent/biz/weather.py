import re
from dataclasses import dataclass
from datetime import datetime

import requests

from config.env_config import config
from config.logger_core import log, trace
from exception.AgentException import AgentException
from exception.error_code import ErrorCode


@dataclass
class Weather:
    city: str
    weather: str
    temperature: str
    wind: str
    query_time: str

    @classmethod
    def __do_query__(cls, city: str) -> "Weather":
        url = config.query_weather_url.format(city=city)
        timeout = config.query_weather_timeout
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            response.encoding="utf-8"
            log.info(f"请求的url：url:{url},timeout:{timeout}, response:{response.text}")
            return Weather.__handle_result__(city, response.text)
        else:
            log.warn(f"查询天气响应状态:{response.status_code}")
            raise AgentException(ErrorCode.WEATHER_ERROR)

    @classmethod
    def __handle_result__(cls, city:str, raw_text: str) -> "Weather":
        weather_match = re.search(r'^([A-Za-z\s]+)', raw_text)  # 取开头的非数字部分（天气状况）
        temp_match = re.search(r'([+-]?\d+)°C', raw_text)  # 取温度数字
        wind_match = re.search(r'(\d+)\s*km/h', raw_text)  # 取风速数字
        weather = weather_match.group(1).strip() if weather_match else "未知"
        temp = temp_match.group(1).strip() if temp_match else "N/A"
        wind = wind_match.group(1).strip() if wind_match else "N/A"
        # 5. 输出结构化结果
        return cls(city, weather, temp, wind, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def query(city:str) -> str:
        try:
            data = Weather.__do_query__(city)
            return (
                f"城市：{data.city}\n"
                f"天气：{data.weather}\n"
                f"温度：{data.temperature}°C\n"
                f"风速：{data.wind} km/h\n"
                f"查询时间：{data.query_time}"
            )
        except Exception as e:
            log.info(f"查询天气异常{e}")
            raise AgentException(ErrorCode.WEATHER_ERROR)

