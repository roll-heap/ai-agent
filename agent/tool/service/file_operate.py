from agent.tool.dao import FileOperateDao
from agent.tool.model import ToolResponseModel
from exception import AgentException


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

    @staticmethod
    def list_directory(directory_path:str, recursive: bool) -> ToolResponseModel:
        """
         获取目录内容。
         recursive=False： 只查看当前目录
         recursive=True： 递归查看子目录
         """
        try:
            result = FileOperateDao.list_directory(directory_path, recursive)
            return ToolResponseModel(data=result)
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))