from agent.tool.dao import CurrentTimeDao
from agent.tool.domain import ToolResponseModel


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
