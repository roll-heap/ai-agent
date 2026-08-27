from pathlib import Path


class FileOperate:
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
        try:
            return file.read_text(encoding="utf-8")
        except Exception as e:
            return f"读取文件失败：{str(e)}"
        return context

    @staticmethod
    def write_file(file_path:str, messages: list):
        """
        写文件
        """
        file = Path(file_path)
        # 确保父目录存在
        file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file, "w", encoding="utf-8") as file:
                for message in messages:
                    file.write(str(message))
            return f"文件写入成功 {file_path}"
        except Exception as e:
            return f"文件写入失败：{str(e)}"
