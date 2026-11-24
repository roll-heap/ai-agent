import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from book.chapter3.user_memory.base_memory_manager import BaseMemoryManager


@dataclass
class MemoryNote:
    """
    simple notes中的一条记忆
    """
    note_id:str
    content:str
    session_id:str
    created_at:str
    update_at:str
    tags:list[str]=field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        将记忆对象转换成可JSON序列化的字典
        """
        return asdict(self)

class SimpleNotesMemoryManager(BaseMemoryManager):
    """基于文本笔记列表的记忆管理系统"""
    def __init__(self, storage_path: Path):
        # 初始化记忆列表和存储路径
        self.storage_path = storage_path
        self.notes:list[MemoryNote]=[]
        # 初始化加载已经保存的记忆
        self.load_memory()

    def load_memory(self) -> None:
        """从json文件加载记忆"""
        if not self.storage_path.exists():
            self.notes=[]
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("记忆文件根节点必须是JSON对象")
            raw_notes = data.get("notes",[])
            if not isinstance(raw_notes, list):
                raise ValueError("notes必须是JSON数组")
            # 将字典转换为memoryNote对象
            self.notes=[MemoryNote(**item) for item in raw_notes]
        except(json.JSONDecodeError, TypeError, KeyError) as exc:
            raise ValueError("记忆文件格式错误，无法加载") from exc

    def save_memory(self) -> None:
        """将记忆写入json文件，使用临时文件避免直接覆盖原文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": 1,
            "notes":[note.to_dict() for note in self.notes]
        }
        temp_path = self.storage_path.with_suffix(self.storage_path.suffix+".tmp")
        try:
            temp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            os.replace(temp_path, self.storage_path)
        finally:
            # 如果写入是不，清理可能残留的临时文件
            if temp_path.exists():
                temp_path.unlink()


    def add_memory(self, content: Any, session_id: str, **kwargs: Any) -> str:
        """新增一条文本记忆并返回记忆ID"""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("记忆内容必须是非空字符串")
        if not session_id.strip():
            raise ValueError("session_id不能为空")
        tags = kwargs.get("tags",[])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("记忆内容必须是非空字符串")
        if not session_id.strip():
            raise ValueError("session_id不能为空")
        tags = kwargs.get("tags",[])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("tags必须是字符串列表")
        note = MemoryNote(
            note_id=str(uuid.uuid4()),
            content=content.strip(),
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            update_at=datetime.now().isoformat(),
            tags = tags.copy()
        )
        self.notes.append(note)
        self.save_memory()
        return note.note_id

    def update_memory(self, memory_id: str, content: Any, session_id: str, **kwargs: Any) -> bool:
        """更新指定记忆，保留原始创建时间"""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("记忆内容必须是非空字符串")
        if not session_id.strip():
            raise ValueError("session_id不能为空")
        for note in self.notes:
            if note.note_id == memory_id:
                note.content = content.strip()
                note.session_id = session_id
                note.update_at = datetime.now().isoformat()
                #没有传入tags时保留原标签
                if "tags" in kwargs:
                    tags = kwargs["tags"]
                    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                        raise ValueError("tags必须是字符串列表")
                    note.tags = tags.copy()

                self.save_memory()
                return True
        return False


    def delete_memory(self, memory_id: str) -> None:
        """根据记忆ID删除记忆"""
        original_count = len(self.notes)
        self.notes=[note for note in self.notes if note.note_id != memory_id]
        # 只有确实删除了记忆才需要写入文件
        if len(self.notes) != original_count:
            self.save_memory()

    def get_context_string(self) -> str:
        """将全部笔记转换为模型可使用的文本上下文"""
        if not self.notes:
            return "No previous memory notes available"
        lines=["User Memory Notes"]
        for index, note in enumerate(self.notes, start=1):
            lines.append(f"{index}. {note.content}")
            if note.tags:
                lines.append(f"  Tags: {', '.join(note.tags)}")
        return "\n".join(lines)

    def search_memories(self, query: str) -> list[Any]:
        """通过内容或标签进行不区分大小写的文本匹配"""
        query=query.strip().casefold()
        if not query:
            return []
        # 关键词字串匹配，不理解语义  note.content.casefold()
        return [note for note in self.notes
                if query in note.content.casefold()
                or any(query in tag.casefold() for tag in note.tags)]


if __name__=="__main__":
    parent_path = Path(__file__).resolve().parent
    path = parent_path / "data" / "simple_notes_test.json"
    manager = SimpleNotesMemoryManager(path)
    note_id = manager.add_memory(
        content="用户目前驾驶2025款本田雅阁",
        session_id="session-001",
        tags=["vehicle"]
    )
    print("新增记忆Id:", note_id)

    search_result = manager.search_memories("本田")
    print("搜索结果：", [item.content for item in search_result])

    # 更新记忆
    updated = manager.update_memory(
        note_id,
        "用户目前驾驶2025款丰田凯美瑞",
        "session-002"
    )
    print("更新成功：", updated)

    # 查看模型上下文
    print(manager.get_context_string())
    # 删除记忆
    manager.delete_memory(note_id)

    # 重新创建对象，验证持久化
    manager = SimpleNotesMemoryManager(path)
    print("重新加载后的记忆数量：", len(manager.notes))