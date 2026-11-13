from agent.tool.dao import WebFetcherDao
from agent.tool.domain import ToolResponseModel
from exception import AgentException


class WebFetcherService:
    @staticmethod
    def web_fetcher(url: str, max_length:int=2000) -> ToolResponseModel:
        """
        抓取网页内容，返回纯文本（限制长度）
        """
        try:
            data = WebFetcherDao.web_fetcher(url, max_length)
            return ToolResponseModel(data=data)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))