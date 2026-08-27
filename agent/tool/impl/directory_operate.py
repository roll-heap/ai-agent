from pathlib import Path


class DirectoryOperate:
    @staticmethod
    def list_directory(directory_path:str) -> str:
        """
        获取指定目录下的文件和文件夹
        :param directory_path:
        :return:
        """
        directory = Path(directory_path)
        if not directory.exists():
            return f"目录不存在：{directory_path}"

        if not directory.is_dir():
            return f"不是目录：{directory_path}"

        try:
            items = []
            for item in directory.iterdir():
                if item.is_file():
                    items.append(f"[文件] {item.name}")
                elif item.is_dir():
                    items.append(f"[目录] {item.name}")
            if not items:
                return "目录为空"

            return "\n".join(items)
        except Exception as e:
            return f"读取目录失败：{str(e)}"