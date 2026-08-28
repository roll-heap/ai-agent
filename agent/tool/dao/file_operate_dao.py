from datetime import datetime
from pathlib import Path

from agent.tool.model.file_metadata_model import FileMetaDataModel


class FileOperateDao:
    @staticmethod
    def read_file(file_path:str):
        """
        读取文件
        """
        file = Path(file_path)
        if not file.exists():
            return f"文件不存在：{file_path}"
        if not file.is_file():
            return f"不是文件：{file_path}"
        return file.read_text(encoding="utf-8")

    @staticmethod
    def write_file(file_path:str, messages: list):
        """
        写文件
        """
        file = Path(file_path)
        # 确保父目录存在
        file.parent.mkdir(parents=True, exist_ok=True)

        with open(file, "w", encoding="utf-8") as file:
            for message in messages:
                file.write(str(message))
        return f"文件写入成功 {file_path}"

    @staticmethod
    def read_metadata(file_path: str) -> FileMetaDataModel:
        file = Path(file_path)

        if not file.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        if not file.is_file():
            raise ValueError(f"不是文件：{file_path}")

        stat = file.stat()

        return FileMetaDataModel(
            name=file.name,
            path=str(file.resolve()),
            suffix=file.suffix,
            size=stat.st_size,
            created_time=datetime.fromtimestamp(stat.st_ctime),
            modified_time=datetime.fromtimestamp(stat.st_mtime)
        )