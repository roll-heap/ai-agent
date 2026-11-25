import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from book.chapter3.user_memory.base_memory_manager import BaseMemoryManager


class JsonCardsMemoryManager(BaseMemoryManager):
    def __init__(self, storage_path:Path):
        # 使用三层嵌套字典保存记忆卡片
        self.storage_path = storage_path
        self.memory_cards:dict[str, dict[str, dict[str, Any]]]={}
        # 初始化加载已经持久化的记忆
        self.load_memory()

    def load_memory(self) -> None:
        if not self.storage_path.exists():
            self.memory_cards={}
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("记忆文件根节点必须是JSON对象")
            memory_cards = data.get("memory_cards", {})
            if not isinstance(memory_cards, dict):
                raise ValueError("memory_cards必须是JSON对象")
            self.memory_cards = memory_cards
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("记忆文件格式错误，无法加载") from exc

    def save_memory(self) -> None:
        """
        将JSON Cards保存到文件，使用临时文件避免直接覆盖
        """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "type":"json_cards",
            "updated_at": datetime.now().isoformat(),
            "memory_cards":self.memory_cards
        }
        temp_path = self.storage_path.with_suffix(self.storage_path.suffix+".tmp")
        try:
            temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            # 原子替换，避免写入中断导致的原文件被截断
            os.replace(temp_path, self.storage_path)
        finally:
            # 写入失败时清理可能残留的临时文件
            if temp_path.exists():
                temp_path.unlink()

    def add_memory(self, content: Any, session_id: str, **kwargs: Any) -> str:
        """新增一张JSON记忆卡片"""
        if not isinstance(content, dict):
            raise ValueError("Json cards的记忆内容必须是字典")
        category = content.get("category","general")
        subcategory = content.get("subcategory","info")
        key = content.get("key", str(uuid.uuid4()))
        value = content.get("value")
        if not all(isinstance(item, str) and item.strip() for item in (category, subcategory, key, session_id)):
            raise ValueError("category, subcategory, key和session_id不能为空")
        self.memory_cards.setdefault(category, {})
        self.memory_cards[category].setdefault(subcategory, {})
        self.memory_cards[category][subcategory][key]={
            "value":value,
            "source":session_id,
            "updated_at":datetime.now().isoformat()
        }
        self.save_memory()
        # 使用层次路径作为记忆ID
        return f"{category}.{subcategory}.{key}"

    def update_memory(self, memory_id: str, content: Any, session_id: str, **kwargs: Any) -> bool:
        """
        更新置顶JSON记忆卡片
        """
        if not isinstance(content, dict):
            raise ValueError("JSON Cards的更新内容必须是字典")
        # 通过category.subcategory.key定位记忆
        parts = memory_id.split(".")
        if len(parts) != 3:
            return False
        category, subcategory, key = parts
        if category not in self.memory_cards or subcategory not in self.memory_cards[category] or key not in self.memory_cards[category][subcategory]:
            return False
        # 更新value、来源和更新时间
        self.memory_cards[category][subcategory][key]={
            "value":content.get("value"),
            "source":session_id,
            "updated_at":datetime.now().isoformat()
        }
        self.save_memory()
        return True


    def delete_memory(self, memory_id: str) -> None:
        """根据层次路径删除一张记忆卡片"""
        parts = memory_id.split(".")
        if len(parts) != 3:
            return
        category, subcategory,key = parts
        if (category not in self.memory_cards
            or subcategory not in self.memory_cards[category]
            or key not in self.memory_cards[category][subcategory]):
            return
        del self.memory_cards[category][subcategory][key]
        # 删除卡片后，清理空的子类别和类别
        if not self.memory_cards[category][subcategory]:
            del self.memory_cards[category][subcategory]
        if not self.memory_cards[category]:
            del self.memory_cards[category]
        self.save_memory()

    def get_context_string(self) -> str:
        """将全部JSON Cards转换为模型上下文"""
        if not self.memory_cards:
            return "No previous memory cards available"
        return "User Memory Cards（Hierarchical JSON）:\n\n" + json.dumps(self.memory_cards, ensure_ascii=False, indent=2)

    def search_memories(self, query: str) -> list[Any]:
        """按照类别，子类别，键和值进行文本匹配"""
        query = query.strip().casefold()
        if not query:
            return []
        results = []
        for category, subcategories in self.memory_cards.items():
            for subcategory, items in subcategories.items():
                for key, data in items.items():
                    memory_path=f"{category}.{subcategories}.{key}"
                    value = str(data.get("value","")).casefold()
                    # 匹配类别，子类别，键或记忆值
                    if (query in category.casefold()
                        or query in subcategory.casefold()
                        or query in key.casefold()
                        or query in value):
                        results.append((memory_path, data))
        return results


if __name__=="__main__":
    # 使用独立测试文件，避免影响Simple Notes的实验数据
    storage_path = Path(__file__).resolve().parent/"data"/"json_cards_test.json"
    manager = JsonCardsMemoryManager(storage_path)
    # 新增一张工作信息卡片
    memory_id = manager.add_memory(
        content={
            "category":"work",
            "subcategory":"company",
            "key":"name",
            "value":"TechCorp"
        },
        session_id="session-001"
    )
    print("新增记忆ID:", memory_id)
    # 检索记忆
    results = manager.search_memories("TechCorp")
    print("检索结果：", results)
    # 更新指定卡片
    updated = manager.update_memory(
        memory_id=memory_id,
        content={"value":"NewTech"},
        session_id="session-002"
    )
    print("更新结果：", updated)
    # 查看模型上下文
    print(manager.get_context_string())
    # 删除卡片
    manager.delete_memory(memory_id)
    # 重新是梨花，检查持久化结果
    manager = JsonCardsMemoryManager(storage_path)
    print("重新加载后的记忆", manager.memory_cards)