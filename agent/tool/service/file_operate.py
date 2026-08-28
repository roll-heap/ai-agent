from agent.tool.dao.file_operate_dao import FileOperateDao
from agent.tool.model.tool_response_model import ToolResponseModel
from exception.agent_exception import AgentException


class FileOperateService:
    @staticmethod
    def read_file(file_path:str) -> ToolResponseModel:
        """
        读取文件
        """
        try:
            result = FileOperateDao.read_file(file_path)
            return ToolResponseModel(data=result)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))

    @staticmethod
    def write_file(file_path:str, content: str) -> ToolResponseModel:
        """
        写文件
        """
        try:
            result = FileOperateDao.write_file(file_path, content)
            return ToolResponseModel(data=result)
        except Exception as e:
            return ToolResponseModel(success=False, msg=f"文件写入失败：{str(e)}")



    @staticmethod
    def read_metadata(file_path: str) -> ToolResponseModel:
        try:
            metadata = FileOperateDao.read_metadata(file_path)
            return ToolResponseModel(data=metadata)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))