from agent.tool.dao import SystemInfoDao
from agent.tool.model import ToolResponseModel


class SystemInfoService:
    @staticmethod
    def system_info() -> ToolResponseModel:
        try:
            data = SystemInfoDao.get_system_info()
            return ToolResponseModel(data=data)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))