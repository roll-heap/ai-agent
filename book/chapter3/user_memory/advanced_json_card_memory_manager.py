import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from book.chapter3.user_memory.base_memory_manager import BaseMemoryManager


class AdvancedJsonCardMemoryManager(BaseMemoryManager):
    """
    Advanced JSON Cards 记忆管理器。

    数据结构：
        categories
            └── category
                 └── card_key
                      └── 完整记忆卡片

    每张卡片包含：
        value       ：具体事实
        backstory   ：事实的来源背景和产生背景
        date_created：卡片记录的创建日期
        person      ：事实涉及的人物
        relationship：人物与用户之间的关系
        _metadata   ：管理元数据
    """

    def __init__(self, storage_path: Path):
        # 使用独立的持久化文件，避免影响基础 JSON Cards。
        self.storage_path = storage_path
        # category -> card_key -> 完整记忆卡片
        self.categories: dict[str, dict[str, dict[str, Any]]] = {}
        # 初始化时加载已有记忆。
        self.load_memory()

    # ========================================================
    # 一、数据校验
    # ========================================================
    @staticmethod
    def _validate_card(card: Any) -> None:
        """校验完整记忆卡片。"""
        if not isinstance(card, dict):
            raise ValueError("Advanced JSON Card 必须是 JSON 对象")
        if "value" not in card or card["value"] is None:
            raise ValueError("记忆卡片必须包含非空 value")
        # backstory 允许为空，但必须是字符串。
        backstory = card.get("backstory")
        if not isinstance(backstory, str):
            raise ValueError("backstory 必须是字符串")
        # 其余字段必须是非空字符串。
        for field in ("date_created", "person", "relationship"):
            value = card.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"记忆卡片字段 {field} 必须是非空字符串")
        try:
            json.dumps(card, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("记忆卡片包含不可 JSON 序列化的数据") from exc

    @staticmethod
    def _build_card(card: dict[str, Any], session_id: str) -> dict[str, Any]:
        """
        构造新增卡片。
        缺少部分辅助字段时，采用书籍配套实现中的默认值。
        """
        result = deepcopy(card)
        now = datetime.now()
        # 以下默认值与书籍配套 AdvancedJSONMemoryManager 保持一致。
        result.setdefault("backstory", "")
        result.setdefault("date_created", now.strftime("%Y-%m-%d %H:%M:%S"))
        result.setdefault("person", "Unknown")
        result.setdefault("relationship", "primary account holder")
        # 内部元数据不作为用户事实内容。
        result["_metadata"] = {
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "source": session_id,
        }
        return result

    # ========================================================
    # 二、持久化
    # ========================================================
    def load_memory(self) -> None:
        """从 JSON 文件加载 Advanced JSON Cards。"""
        if not self.storage_path.exists():
            self.categories = {}
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("记忆文件根节点必须是 JSON 对象")
            categories = data.get("categories", {})
            if not isinstance(categories, dict):
                raise ValueError("categories 必须是 JSON 对象")
            # 校验两层结构，避免加载后出现无法操作的数据。
            for category, cards in categories.items():
                if not isinstance(category, str) or not category.strip():
                    raise ValueError("category 必须是非空字符串")
                if not isinstance(cards, dict):
                    raise ValueError(f"category={category} 下的卡片集合必须是 JSON 对象")
                for card_key, card in cards.items():
                    if not isinstance(card_key, str) or not card_key.strip():
                        raise ValueError("card_key 必须是非空字符串")
                    if not isinstance(card, dict):
                        raise ValueError(f"卡片 {category}.{card_key} 必须是 JSON 对象")
            self.categories = categories
        except json.JSONDecodeError as exc:
            raise ValueError("Advanced JSON Cards 文件不是合法 JSON") from exc

    def save_memory(self) -> None:
        """
        保存记忆。
        使用临时文件和 os.replace，避免直接覆盖时发生文件截断。
        """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "type": "advanced_json_cards",
            "updated_at": datetime.now().isoformat(),
            "categories": self.categories,
        }
        temp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        try:
            temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            # 原子替换持久化文件。
            os.replace(temp_path, self.storage_path)
        finally:
            # 保存失败时清理临时文件。
            if temp_path.exists():
                temp_path.unlink()

    # ========================================================
    # 三、新增记忆
    # ========================================================
    def add_memory(self, content: Any, session_id: str, **kwargs: Any) -> str:
        """
        新增一张 Advanced JSON Card。
        content 格式：
        {
            "category": "subscription",
            "card_key": "netflix",
            "card": {
                "value": "...",
                "backstory": "...",
                "person": "...",
                "relationship": "..."
            }
        }
        """
        if not isinstance(content, dict):
            raise ValueError("新增内容必须是 JSON 对象")
        category = content.get("category", "general")
        card_key = content.get("card_key")
        card = content.get("card")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("category 必须是非空字符串")
        if "." in category:
            raise ValueError("category 不能包含 '.'，以保证记忆 ID 可解析")
        if not isinstance(card_key, str) or not card_key.strip():
            raise ValueError("新增记忆必须提供稳定的 card_key")
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id 必须是非空字符串")
        if card_key in self.categories.get(category, {}):
            raise ValueError(f"记忆卡片已经存在：{category}.{card_key}")
        if not isinstance(card, dict):
            raise ValueError("content.card 必须是 JSON 对象")
        # 构造卡片并填充默认字段。
        new_card = self._build_card(card, session_id)
        # 校验最终卡片。
        self._validate_card(new_card)
        # 使用稳定的 category + card_key 定位业务对象。
        self.categories.setdefault(category, {})
        self.categories[category][card_key] = new_card
        self.save_memory()
        return f"{category}.{card_key}"

    # ========================================================
    # 四、更新记忆
    # ========================================================
    def update_memory(self, memory_id: str, content: Any, session_id: str, **kwargs: Any) -> bool:
        """
        更新已有记忆卡片。

        当前采用完整卡片替换策略：
        1. 必须提供完整卡片。
        2. 校验通过后才替换。
        3. 保留原始 created_at。
        4. 更新 updated_at 和 source。
        """
        if not isinstance(content, dict):
            raise ValueError("更新内容必须是 JSON 对象")
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id 必须是非空字符串")
        # 只按第一个点拆分，允许 card_key 本身包含点。
        parts = memory_id.split(".", 1)
        if len(parts) != 2:
            return False
        category, card_key = parts
        old_card = self.categories.get(category, {}).get(card_key)
        if old_card is None:
            return False
        # 更新接口只接受完整卡片，不接受不完整字段集合。
        new_card = content.get("card")
        self._validate_card(new_card)
        # 复制数据，避免修改调用方传入的对象。
        new_card = deepcopy(new_card)
        now = datetime.now().isoformat()
        old_metadata = old_card.get("_metadata", {})
        # 保留创建时间，更新修改时间和来源。
        new_card["_metadata"] = {
            "created_at": old_metadata.get("created_at", now),
            "updated_at": now,
            "source": session_id,
        }
        # 只有校验全部通过后，才替换旧卡片。
        self.categories[category][card_key] = new_card
        self.save_memory()
        return True

    # ========================================================
    # 五、删除记忆
    # ========================================================
    def delete_memory(self, memory_id: str) -> None:
        """根据 category.card_key 删除指定卡片。"""
        parts = memory_id.split(".", 1)
        if len(parts) != 2:
            return
        category, card_key = parts
        if category not in self.categories:
            return
        if card_key not in self.categories[category]:
            return
        del self.categories[category][card_key]
        # 删除卡片后清理空分类。
        if not self.categories[category]:
            del self.categories[category]
        self.save_memory()

    # ========================================================
    # 六、上下文转换
    # ========================================================
    def get_context_string(self) -> str:
        """
        将记忆卡片转换为模型上下文。
        不向模型暴露内部 _metadata。
        """
        if not self.categories:
            return "No previous advanced memory cards available."
        context = "User Memory Cards (Advanced JSON Structure):\n\n"
        for category, cards in self.categories.items():
            context += f"Category: {category}\n"
            for card_key, card in cards.items():
                # 不将管理元数据作为用户事实交给模型。
                display_card = {
                    key: value
                    for key, value in card.items()
                    if key != "_metadata"
                }
                context += f"  Card '{card_key}':\n"
                context += (json.dumps(display_card, ensure_ascii=False, indent=4) + "\n")
        return context

    # ========================================================
    # 七、记忆检索
    # ========================================================
    def search_memories(self, query: str) -> list[Any]:
        """
        按 category、card_key 和卡片内容进行子字符串匹配。
        注意：这里沿用当前 JSON Cards 的检索思路，
        并不属于向量检索或语义检索。
        """
        if not isinstance(query, str):
            raise ValueError("检索关键词必须是字符串")
        query = query.strip().casefold()
        if not query:
            return []
        results = []
        for category, cards in self.categories.items():
            for card_key, card in cards.items():
                # 不将内部管理元数据纳入用户事实检索。
                searchable_card = {
                    key: value
                    for key, value in card.items()
                    if key != "_metadata"
                }

                card_text = json.dumps(searchable_card, ensure_ascii=False).casefold()

                if (
                        query in category.casefold()
                        or query in card_key.casefold()
                        or query in card_text
                ):
                    memory_id = f"{category}.{card_key}"
                    results.append((memory_id, card))

        return results


if __name__ == "__main__":
    # 使用独立测试文件，避免影响基础 JSON Cards 的实验数据
    storage_path = Path(__file__).resolve().parent / "data" / "advanced_json_cards_test.json"
    manager = AdvancedJsonCardMemoryManager(storage_path)
    # 新增 Netflix 订阅记忆
    netflix_id = manager.add_memory(
        content={
            "category": "subscription",
            "card_key": "netflix",
            "card": {
                "value": "Netflix subscription is active",
                "backstory": (
                    "John, the user's father, originally subscribed "
                    "to Netflix. The user paid for it."
                ),
                "date_created": "2026-11-25",
                "person": "John",
                "relationship": "father",
            },
        },
        session_id="session-001",
    )
    print("新增 Netflix 记忆ID:", netflix_id)
    # 新增 Disney+ 订阅记忆
    disney_id = manager.add_memory(
        content={
            "category": "subscription",
            "card_key": "disney_plus",
            "card": {
                "value": "Disney+ subscription is active",
                "backstory": "The user subscribed to Disney+ for personal use.",
                "date_created": "2026-11-25",
                "person": "User",
                "relationship": "primary account holder",
            },
        },
        session_id="session-001",
    )
    print("新增 Disney+ 记忆ID:", disney_id)
    # 检索 Netflix 记忆
    results = manager.search_memories("Netflix")
    print("Netflix 检索结果：", results)
    # 更新 Netflix：订阅已经取消
    updated = manager.update_memory(
        memory_id=netflix_id,
        content={
            "card": {
                "value": "Netflix subscription has been cancelled",
                "backstory": (
                    "John, the user's father, originally subscribed "
                    "to Netflix. The user paid for it. "
                    "The subscription was later cancelled."
                ),
                "date_created": "2026-11-25",
                "person": "John",
                "relationship": "father",
            }
        },
        session_id="session-002",
    )
    print("Netflix 更新结果：", updated)
    # 查看模型上下文，检查两张卡片是否都存在
    print("\n更新后的记忆上下文：")
    print(manager.get_context_string())
    # 删除 Netflix 记忆
    manager.delete_memory(netflix_id)
    # 重新实例化管理器，检查持久化结果
    manager = AdvancedJsonCardMemoryManager(storage_path)
    print("\n重新加载后的记忆：")
    print(manager.get_context_string())
