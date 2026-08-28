from agent.tool.dao.date_current_dao import CurrentTimeDao
from agent.tool.model.tool_response_model import ToolResponseModel


class CurrentTimeService:
    @staticmethod
    def current_time() -> ToolResponseModel:
        """
           获取当前日期和时间。
        """
        try:
            current_time = CurrentTimeDao.current_time()
            return ToolResponseModel(data=current_time)
        except Exception as e:
            return ToolResponseModel(success=False, data=None, msg=str(e))
