from agent.tool.dao.directory_operate_dao import DirectoryOperateDao
from agent.tool.model.tool_response_model import ToolResponseModel
from exception.agent_exception import AgentException


class DirectoryOperateService:
    @staticmethod
    def list_directory(directory_path:str, recursive: bool) -> ToolResponseModel:
        """
         获取目录内容。
         recursive=False： 只查看当前目录
         recursive=True： 递归查看子目录
         """
        try:
            result = DirectoryOperateDao.list_directory(directory_path, recursive)
            return ToolResponseModel(data=result)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))


