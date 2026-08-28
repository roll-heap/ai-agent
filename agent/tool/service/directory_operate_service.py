from agent.tool.dao.directory_operate_dao import DirectoryOperateDao


class DirectoryOperateService:
    @staticmethod
    def list_directory(directory_path:str, recursive: bool) -> dict:
        """
         获取目录内容。
         recursive=False： 只查看当前目录
         recursive=True： 递归查看子目录
         """
        try:
            result = DirectoryOperateDao.list_directory(directory_path, recursive)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "data": str(e)
            }
