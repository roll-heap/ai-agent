import requests
from bs4 import BeautifulSoup

from agent.tool.dao.web_fetcher_dao import WebFetcherDao


class WebFetcherService:
    @staticmethod
    def web_fetcher(url: str, max_length:int=2000) -> dict:
        """
        抓取网页内容，返回纯文本（限制长度）
        """
        try:
            data = WebFetcherDao.web_fetcher(url, max_length)
            return {
                "success": True,
                "data": data
            }
        except Exception as e:
            return {
                "success": False,
                "data": f"抓取网页异常：{str(e)}"
            }

