# ============================================================
# 3、 LangChain Tool 封装Tool
# ============================================================
from langchain.tools import tool

from agent.tool.service.calculater_service import CalculaterService
from agent.tool.service.date_current_service import CurrentTimeService
from agent.tool.service.file_operate import FileOperateService
from agent.tool.service.system_info_service import SystemInfoService
from agent.tool.service.system_resource_service import SystemResourceService
from agent.tool.service.weather import WeatherService
from agent.tool.service.web_fetcher import WebFetcherService


@tool(name_or_callable="weather_tool", description="""
查询某个城市的实时天气。

参数：
city：城市名称，例如“上海”“北京”“New York”。

返回：
当前天气状况、温度、风速和查询时间。

当用户询问天气时使用此工具。
"""
)
def weather_tool(city: str) -> dict:
    model = WeatherService.query_weather(city)
    return model.model_dump(mode="json")


@tool(name_or_callable="calculate_tool", description="""
执行数学计算。

参数：
expression：数学表达式，例如：
3 + 5 * 2
(8 + 2) * 3
10 / 2

当用户要求进行数学计算时使用此工具。
"""
)
def calculate_tool(expression: str) -> dict:
    model = CalculaterService.calculater(expression)
    return model.model_dump(mode="json")


@tool(name_or_callable="current_time_tool", description="""
获取当前日期和时间。

不需要参数。

当用户询问现在几点、当前时间、今天日期时使用此工具。
"""
)
def current_time_tool() -> dict:
    model = CurrentTimeService.current_time()
    return model.model_dump(mode="json")


@tool(name_or_callable="fetch_webpage_tool", description="""
抓取指定 URL 网页中的文本内容。

参数：
url：需要访问的网页 URL。

当用户要求读取、分析某个网页内容时使用此工具。
"""
)
def fetch_webpage_tool(url: str) -> dict:
    model = WebFetcherService.web_fetcher(url)
    return model.model_dump(mode="json")


@tool(name_or_callable="list_directory_tool", description="""
获取指定目录中的文件和子目录。

参数：
directory_path：需要查看的目录路径。
recursive：是否递归查看子目录。

false：只查看当前目录。
true：递归查看所有子目录。

当用户要求查看目录内容、查看有哪些文件、
查找文件、查看项目结构时使用此工具。
"""
)
def list_directory_tool(directory_path: str, recursive: bool) -> dict:
    model = FileOperateService.list_directory(directory_path, recursive)
    return model.model_dump(mode="json")


@tool(name_or_callable="read_file_tool", description="""
读取指定路径的文件内容。

参数：
file_path：文件路径。

当用户要求读取文件内容时使用此工具。
不适用于 PDF、图片、Word、Excel 等二进制或需要专用解析器的文件。
"""
)
def read_file_tool(file_path: str) -> dict:
    model = FileOperateService.read_file(file_path)
    return model.model_dump(mode="json")


@tool(name_or_callable="write_file_tool", description="""
将文本写入指定文件。

参数：
file_path：文件路径。
messages：需要写入的文本内容列表。

当用户明确要求创建或写入文件时使用此工具。
"""
)
def write_file_tool(file_path: str, content: str) -> dict:
    model = FileOperateService.write_file(file_path, content)
    return model.model_dump(mode="json")


@tool(name_or_callable="read_file_metadata_tool", description="""
获取指定文件的元数据信息。

参数：
file_path：需要查询的文件路径。

返回：
文件名、完整路径、文件后缀、文件大小、
文件创建时间和最后修改时间。

当用户询问某个文件的信息、属性、大小、
创建时间或修改时间时使用此工具。
"""
)
def read_file_metadata_tool(file_path: str) -> dict:
    model = FileOperateService.read_metadata(file_path)
    return model.model_dump(mode="json")

@tool(name_or_callable="system_info_tool", description="""获取系统信息，当用户询问系统信息的时候使用此工具""")
def system_info_tool() -> dict:
    model = SystemInfoService.system_info()
    return model.model_dump(mode="json")

@tool(name_or_callable="system_resource_tool", description="""获取系统资源，当用户询问系统使用资源的时候使用此工具""")
def system_resource_tool() -> dict:
    model = SystemResourceService.system_resource()
    return model.model_dump(mode="json")

tools = [
    weather_tool,
    calculate_tool,
    current_time_tool,
    fetch_webpage_tool,
    read_file_tool,
    write_file_tool,
    list_directory_tool,
    read_file_metadata_tool,
    system_info_tool,
]
