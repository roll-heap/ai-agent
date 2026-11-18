from pathlib import Path


class AgentUtils:
    @staticmethod
    def get_project_root(project_name) -> Path:
        """从当前文件位置向上查找，直到找到项目标记文件，返回其父目录作为项目根目录。"""
        current_path = Path(__file__).resolve().parent

        # 从当前目录开始，逐级向上遍历所有父目录
        for parent in [current_path, *current_path.parents]:
            # 如果当前目录下存在任何一个标记文件，则判定其为项目根目录
            if parent.name == "ai-agent":
                return parent

        # 如果一直找到文件系统根目录都没找到，可以抛错或返回一个默认值
        raise FileNotFoundError(f"未找到项目根目录，查找的标记文件为: {project_name}")