from agent.tool.dao import SearchWebDao
from agent.tool.domain import ToolResponseModel


class SearchWebService:
    @staticmethod
    def search_web(query: str, max_results: int = 5) -> ToolResponseModel:
        try:
            model = SearchWebDao.search_web(query, max_results)
            if not model:
                return ToolResponseModel(data=None, msg="暂无内容")
            return ToolResponseModel(data=model)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))

