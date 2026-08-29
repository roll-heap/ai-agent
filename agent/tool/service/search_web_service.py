from agent.tool.dao.search_web_dao import SearchWebDao
from agent.tool.model.tool_response_model import ToolResponseModel


class SearchWebService:
    @staticmethod
    def search_web(keywords: str, max_results: int = 5) -> ToolResponseModel:
        try:
            model = SearchWebDao.search_web(keywords, max_results)
            if not model:
                return ToolResponseModel(data=None, msg="暂无内容")
            return ToolResponseModel(data=model)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))

