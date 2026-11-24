from abc import ABC, abstractmethod
from typing import Any


class BaseMemoryManager(ABC):
    """
    四种记忆格式公用的抽象管理接口

    具体记忆管理器负责实现不同格式的数据组织、加载、保存、增删改查和上下文转换
    """
    @abstractmethod
    def load_memory(self) -> None:
        pass

    @abstractmethod
    def save_memory(self) -> None:
        pass

    @abstractmethod
    def add_memory(self, content: Any, session_id: str, **kwargs: Any) ->str:
        """
        新增一条记忆
        content：可以是字符串、段落或结构化数据，具体由不同记忆格式决定
        返回新记忆的唯一标识
        """
        pass

    @abstractmethod
    def update_memory(self, memory_id: str, content: Any, session_id:str,**kwargs:Any) -> bool:
        pass

    @abstractmethod
    def delete_memory(self, memory_id:str) -> None:
        pass

    @abstractmethod
    def get_context_string(self) -> str:
        """将当前记忆转换为可注入模型上下文的文本"""
        pass

    @abstractmethod
    def search_memories(self, query:str) -> list[Any]:
        """根据查下条件搜索相关记忆"""
        pass



