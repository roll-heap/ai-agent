from datetime import datetime
from pathlib import Path

from agent.tool.dao.file_operate_dao import FileOperateDao
from agent.tool.model.file_metadata_model import FileMetaDataModel


class FileOperateService:
    @staticmethod
    def read_file(file_path:str) -> dict:
        """
        读取文件
        """
        try:
            result = FileOperateDao.read_file(file_path)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "data": f"读取文件失败：{str(e)}"
            }

    @staticmethod
    def write_file(file_path:str, messages: list) -> dict:
        """
        写文件
        """
        try:
            result = FileOperateDao.write_file(file_path, messages)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "data": f"文件写入失败：{str(e)}"
            }



    @staticmethod
    def read_metadata(file_path: str) -> dict:
        try:
            metadata = FileOperateDao.read_metadata(file_path)
            return {
                "success": True,
                "data": metadata.model_dump(mode="json")
            }
        except Exception as e:
            return {
                "success": False,
                "data": str(e)
            }
