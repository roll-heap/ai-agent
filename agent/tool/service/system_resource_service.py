from agent.tool.dao import SystemResourceDao
from agent.tool.model import ToolResponseModel


class SystemResourceService:
    @staticmethod
    def system_resource() -> ToolResponseModel:
        try:
            data = SystemResourceDao.system_resource()
            return ToolResponseModel(data=data)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))
