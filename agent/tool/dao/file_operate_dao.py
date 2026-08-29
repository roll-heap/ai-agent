from datetime import datetime
from pathlib import Path

from agent.tool.model.file_metadata_model import FileMetaDataModel
from exception.agent_exception import AgentException


class FileOperateDao:
    @staticmethod
    def read_file(file_path:str):
        """
        读取文件
        """
        file = Path(file_path)
        if not file.exists():
            raise AgentException(f"文件不存在：{file_path}")
        if not file.is_file():
            raise AgentException(f"不是文件：{file_path}")
        return file.read_text(encoding="utf-8")

    @staticmethod
    def write_file(file_path:str, content: str):
        """
        写文件
        """
        file = Path(file_path)
        # 确保父目录存在
        file.parent.mkdir(parents=True, exist_ok=True)

        with open(file, "w", encoding="utf-8") as f:
            f.write(f"{content}\n")
        return f"文件写入成功 {file_path}"

    @staticmethod
    def read_metadata(file_path: str) -> FileMetaDataModel:
        file = Path(file_path)

        if not file.exists():
            raise AgentException(f"文件不存在：{file_path}")

        if not file.is_file():
            raise AgentException(f"不是文件：{file_path}")

        stat = file.stat()

        return FileMetaDataModel(
            name=file.name,
            path=str(file.resolve()),
            suffix=file.suffix,
            size=stat.st_size,
            created_time=datetime.fromtimestamp(stat.st_ctime),
            modified_time=datetime.fromtimestamp(stat.st_mtime)
        )

    # Agent
    # 分析项目时通常不需要的目录
    IGNORE_DIRS = {
        ".git",
        ".idea",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules"
    }

    @staticmethod
    def list_directory(directory_path: str, recursive: bool) -> str:
        """
         获取目录内容。
         recursive=False： 只查看当前目录
         recursive=True： 递归查看子目录
         """
        directory = Path(directory_path)
        if not directory.exists():
            raise AgentException(f"目录不存在：{directory_path}")
        if not directory.is_dir():
            raise AgentException(f"不是目录：{directory_path}")
        if recursive:
            items = directory.rglob("*")
        else:
            items = directory.iterdir()

        result = []
        for item in items:
            # 过滤隐藏文件
            if item.name.startswith(".") or any(part in FileOperateDao.IGNORE_DIRS for part in item.parts):
                continue

            relative_path = item.relative_to(directory)
            if item.is_file():
                result.append(f"[文件]{relative_path}")
            elif item.is_dir():
                result.append(f"[目录]{relative_path}")

        if not result:
            raise AgentException("目录为空")
        return "\n".join(result)
