# ============================================================
# 3、 LangChain Tool 封装Tool
# ============================================================
from langchain.tools import tool
from pydantic import BaseModel

from agent.tool.impl.calculater import calculater
from agent.tool.impl.date_current import CurrentTime
from agent.tool.impl.directory_operate import DirectoryOperate
from agent.tool.impl.file_operate import FileOperate
from agent.tool.impl.weather import Weather
from agent.tool.impl.web_fetcher import WebFetcher
from config.logger_core import log


# ============================================================
# 天气查询
# ============================================================
class WeatherResult(BaseModel):
    success: bool
    weather: Weather | None = None
    error: str | None = None



"""
description=...
不是普通注释。
它实际上是在告诉 LLM：
“我这个 Tool 是干什么的，什么时候应该调用我。”
所以以后你设计 Agent，Tool Description 是非常重要的
"""
@tool(name_or_callable="weather_tool", description="""查询某个城市的实时天气。
参数：
city：城市名称，例如“上海”“北京”“New York”。
返回：
当前天气状况、温度、风速和查询时间。
如果要回复今日时间，请调用获取当前时间工具
当用户询问天气时使用此工具。""")
def weather_tool(city) -> WeatherResult:
    """
     查询某个城市的天气。
     参数:
         city: 城市名称，例如 "上海"
     """
    try:
        weather = Weather.query_weather(city)
        return WeatherResult(success=True, weather=weather)
    except Exception as e:
        log.info(f"查询天气失败: {e}")
        return WeatherResult(success=False, error=str(e))


# ============================================================
# 新工具 1：安全计算器
# ============================================================
@tool(name_or_callable="calculate_tool", description="""执行数学计算。
参数：
expression：数学表达式，例如：
3 + 5 * 2
(8 + 2) * 3
10 / 2
当用户要求进行数学计算时使用此工具。""")
def calculate_tool(expression:str) -> str:
    try:
        return calculater(expression)
    except Exception as e:
        return f"计算器计算失败{str(e)}"


# ============================================================
# 新工具 2：获取当前时间
# ============================================================
@tool(name_or_callable="current_time_tool", description="""获取当前日期和时间。
不需要参数。
当用户询问现在几点、当前时间、今天日期时使用此工具。""")
def current_time_tool() -> str:
    try:
         current = CurrentTime.current_time()
         print(f"当前时间：{current}")
         return current
    except Exception as e:
        return f"获取当前时间异常：{str(e)}"

@tool(name_or_callable="fetch_webpage_tool", description="""抓取指定 URL 网页中的文本内容。

参数：
url：需要访问的网页 URL。

当用户要求读取、分析某个网页内容时使用此工具。""")
def fetch_webpage_tool(url: str) -> str:
    try:
        return WebFetcher.web_fetcher(url)
    except Exception as e:
        return f"抓取网页异常：{str(e)}"

@tool(name_or_callable="read_file_tool", description="""读取指定路径的文件内容。
参数：
file_path：文件路径。
当用户要求读取文件内容时使用此工具。""")
def read_file_tool(file_path: str):
    try:
        return FileOperate.read_file(file_path)
    except Exception as e:
        return f"读取文件异常,{str(e)}"

@tool(name_or_callable="write_file_tool", description="""将文本写入指定文件。
参数：
file_path：文件路径。
messages：需要写入的文本内容列表。
当用户明确要求创建或写入文件时使用此工具。""")
def write_file_tool(file_path: str, messages:list):
    try:
        return FileOperate.write_file(file_path, messages)
    except Exception as e:
        return f"写入文件失败，失败信息:{str(e)}"


@tool(name_or_callable="list_directory_tool",description="""获取指定目录中的文件和子目录。
参数：
directory_path：需要查看的目录路径。
当用户要求查看目录内容、查看文件列表、
查找目录中的文件时使用此工具。
"""
)
def list_directory_tool(directory_path: str) -> str:
    try:
        return DirectoryOperate.list_directory(directory_path)
    except Exception as e:
        return f"读取目录失败：{str(e)}"

tools = [
    weather_tool,
    calculate_tool,
    current_time_tool,
    fetch_webpage_tool,
    read_file_tool,
    write_file_tool,
    list_directory_tool
]