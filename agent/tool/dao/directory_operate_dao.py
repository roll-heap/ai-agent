from pathlib import Path


class DirectoryOperateDao:
    #Agent
    #分析项目时通常不需要的目录
    IGNORE_DIRS = {
        ".git",
        ".idea",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules"
    }
    @staticmethod
    def list_directory(directory_path:str, recursive: bool) -> str:
        """
         获取目录内容。
         recursive=False： 只查看当前目录
         recursive=True： 递归查看子目录
         """
        directory = Path(directory_path)
        if not directory.exists():
            return f"目录不存在：{directory_path}"
        if not directory.is_dir():
            return f"不是目录：{directory_path}"
        if recursive:
            items = directory.rglob("*")
        else:
            items = directory.iterdir()

        result = []
        for item in items:
            # 过滤隐藏文件
            if item.name.startswith(".") or any(part in DirectoryOperateDao.IGNORE_DIRS for part in item.parts):
                continue

            relative_path = item.relative_to(directory)
            if item.is_file():
                result.append(f"[文件]{relative_path}")
            elif item.is_dir():
                result.append(f"[目录]{relative_path}")

        if not result:
            return "目录为空"
        return "\n".join(result)
