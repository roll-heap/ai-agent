
"""
实验 3-2：JSON Cards 连续对话记忆更新

本实验使用项目中已有的 layer2_04_multiple_subscriptions.yaml。
每次运行只处理一段会话：
1. 读取当前持久化记忆。
2. 读取指定会话的原始对话。
3. 将旧记忆和新对话交给 LLM。
4. 让 LLM 返回更新后的完整记忆卡片。
5. 对比新旧记忆，通过现有管理器 CRUD 操作保存。
6. 输出更新后的记忆，供人工检查。

运行方式：
python -m book.chapter3.user_memory.step10_json_cards_subscription_update --session-index 1
"""

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import SystemMessage, HumanMessage

from book.chapter3.user_memory.json_card_memory_manager import (
    JsonCardsMemoryManager,
)
from book.chapter3.user_memory.step8_json_card_generation import (
    init_chat_model,
    extract_text,
)


# ============================================================
# 一、实验文件路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# 直接读取项目中已有的 60 个测试用例，不修改原始数据。
DATASET_PATH = (
    BASE_DIR
    / "test_cases"
    / "layer2"
    / "04_multiple_subscriptions.yaml"
)

# 使用独立持久化文件，避免污染之前的偏好记忆实验。
STORAGE_PATH = BASE_DIR / "data" / "json_cards_subscription_test.json"


# ============================================================
# 二、记忆更新 Prompt
# ============================================================

SYSTEM_PROMPT = """
你是一个长期用户记忆维护助手。

你的任务是：
根据已有记忆和最新一段对话，生成更新后的完整 JSON Cards 记忆状态。

请遵守以下要求：

1. 只保存对未来交互有价值的用户事实。
2. 保留已有记忆中仍然有效的信息。
3. 新对话提供了新的独立事实时，应在原有记忆基础上增加信息。
4. 只有新对话明确纠正或改变了旧事实时，才更新对应事实。
5. 不要因为新对话讨论了新的订阅服务，就删除其他仍然有效的订阅记录。
6. 区分当前实际订阅和对话中讨论过的备选方案。
7. 保留订阅名称、当前套餐、月费、账单日期及明确讨论过的优惠信息。
8. 不要将客服提出但用户没有接受的建议记录为用户已经执行的决定。
9. 不要编造对话中没有出现的事实。
10. 返回完整记忆状态，而不是只返回本轮新增的卡片。

每张卡片必须包含以下字段：

{
    "category": "记忆类别",
    "subcategory": "记忆子类别",
    "key": "记忆键",
    "value": "记忆内容"
}

字段要求：
- category、subcategory、key 必须是非空字符串。
- 这三个字段中不要使用英文句点，以保证记忆 ID 可以正确定位。
- value 使用简洁、完整的字符串表达事实。

输出格式：

{
    "cards": [
        {
            "category": "...",
            "subcategory": "...",
            "key": "...",
            "value": "..."
        }
    ]
}

只输出合法 JSON，不要输出 Markdown 代码块或解释。
"""


# ============================================================
# 三、读取原始实验数据
# ============================================================

def load_test_case() -> dict[str, Any]:
    """读取书中对应的原始 YAML 测试用例。"""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"实验数据文件不存在：{DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("实验数据根节点必须是 YAML 对象")

    histories = data.get("conversation_histories")

    if not isinstance(histories, list) or len(histories) != 3:
        raise ValueError("订阅实验必须包含三段原始会话")

    return data


def format_conversation(history: dict[str, Any]) -> str:
    """将一段原始会话转换成模型输入文本。"""

    conversation_id = history.get("conversation_id")
    timestamp = history.get("timestamp")
    metadata = history.get("metadata", {})
    messages = history.get("messages", [])

    if not conversation_id or not isinstance(messages, list):
        raise ValueError("会话数据缺少必要字段")

    role_mapping = {
        "user": "用户",
        "assistant": "客服",
    }

    lines = [
        f"会话 ID：{conversation_id}",
        f"会话时间：{timestamp}",
        f"会话元数据：{json.dumps(metadata, ensure_ascii=False)}",
        "",
    ]

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role not in role_mapping:
            continue

        if not isinstance(content, str):
            raise ValueError("对话消息内容必须是字符串")

        lines.append(f"{role_mapping[role]}：{content}")

    return "\n".join(lines)


# ============================================================
# 四、解析模型返回的完整记忆状态
# ============================================================

def generate_updated_cards(
    model: Any,
    current_memory: dict[str, Any],
    conversation: str,
) -> list[dict[str, str]]:
    """根据旧记忆和新对话生成完整记忆卡片。"""

    prompt = f"""
下面是当前已经保存的记忆：

<current_memory>
{json.dumps(current_memory, ensure_ascii=False, indent=2)}
</current_memory>

下面是最新一段对话：

<new_conversation>
{conversation}
</new_conversation>

请根据已有记忆和最新对话，生成更新后的完整 JSON Cards。
"""

    response = model.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    generated_text = extract_text(response.content)

    try:
        result = json.loads(generated_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"模型返回的内容不是合法 JSON：{generated_text}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("模型返回结果必须是 JSON 对象")

    cards = result.get("cards")

    if not isinstance(cards, list) or not cards:
        raise ValueError("模型没有返回有效的记忆卡片")

    # 校验每张卡片，避免非法路径影响持久化操作。
    required_fields = {"category", "subcategory", "key", "value"}

    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise ValueError(f"第 {index + 1} 张卡片不是对象")

        if not required_fields.issubset(card):
            raise ValueError(f"第 {index + 1} 张卡片字段不完整")

        for field in ("category", "subcategory", "key", "value"):
            value = card[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"第 {index + 1} 张卡片的 {field} 必须是非空字符串"
                )

        for field in ("category", "subcategory", "key"):
            if "." in card[field]:
                raise ValueError(
                    f"第 {index + 1} 张卡片的 {field} 不能包含英文句点"
                )

    return cards


# ============================================================
# 五、将嵌套记忆转换为路径映射
# ============================================================

def flatten_memory(
    memory_cards: dict[str, Any],
) -> dict[str, Any]:
    """将三级嵌套结构转换为 memory_id -> value 的映射。"""

    result = {}

    for category, subcategories in memory_cards.items():
        for subcategory, items in subcategories.items():
            for key, data in items.items():
                memory_id = f"{category}.{subcategory}.{key}"
                result[memory_id] = data.get("value")

    return result


def build_card_map(
    cards: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """将模型输出的卡片转换为以记忆 ID 为键的映射。"""

    result = {}

    for card in cards:
        memory_id = (
            f"{card['category']}."
            f"{card['subcategory']}."
            f"{card['key']}"
        )

        if memory_id in result:
            raise ValueError(f"模型返回了重复的记忆 ID：{memory_id}")

        result[memory_id] = card

    return result


# ============================================================
# 六、通过现有管理器 CRUD 保存更新后的完整状态
# ============================================================

def sync_memory(
    manager: JsonCardsMemoryManager,
    cards: list[dict[str, str]],
    session_id: str,
) -> None:
    """
    对比新旧记忆状态，并调用现有管理器完成新增、更新和删除。

    注意：
    本实验使用独立 JSON 文件，删除操作不会影响其他实验数据。
    """

    old_memory = flatten_memory(manager.memory_cards)
    new_cards = build_card_map(cards)

    new_memory_ids = set(new_cards)
    old_memory_ids = set(old_memory)

    # 新增或更新模型返回的卡片。
    for memory_id, card in new_cards.items():

        if memory_id not in old_memory:
            manager.add_memory(
                content=card,
                session_id=session_id,
            )
            print(f"[新增] {memory_id}")

        elif old_memory[memory_id] != card["value"]:
            manager.update_memory(
                memory_id=memory_id,
                content={"value": card["value"]},
                session_id=session_id,
            )
            print(f"[更新] {memory_id}")

    # 模型返回的完整状态中不存在的旧卡片将被删除。
    for memory_id in old_memory_ids - new_memory_ids:
        manager.delete_memory(memory_id)
        print(f"[删除] {memory_id}")


# ============================================================
# 七、执行指定轮次
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="JSON Cards 连续对话更新实验"
    )

    parser.add_argument(
        "--session-index",
        type=int,
        choices=[1, 2, 3],
        required=True,
        help="本次要处理的会话序号：1=Netflix，2=Disney+，3=Max",
    )

    args = parser.parse_args()

    # 1. 读取原始测试用例。
    test_case = load_test_case()
    history = test_case["conversation_histories"][
        args.session_index - 1
    ]

    session_id = history["conversation_id"]

    # 2. 加载已有记忆。
    manager = JsonCardsMemoryManager(STORAGE_PATH)

    if args.session_index == 1 and manager.memory_cards:
        raise RuntimeError(
            "第一轮实验要求使用空记忆。"
            "当前实验文件已有数据，请确认是否需要重新开始实验。"
        )

    if args.session_index > 1 and not manager.memory_cards:
        raise RuntimeError(
            "当前没有上一轮记忆，请先完成前一轮实验。"
        )

    # 防止重复执行同一会话导致重复提取。
    for subcategories in manager.memory_cards.values():
        for items in subcategories.values():
            for data in items.values():
                if data.get("source") == session_id:
                    raise RuntimeError(
                        f"会话 {session_id} 已经处理过，请勿重复执行。"
                    )

    # 3. 初始化模型。
    model = init_chat_model()

    # 4. 格式化本轮原始对话。
    conversation = format_conversation(history)

    # 5. 根据已有记忆和新对话生成完整记忆状态。
    updated_cards = generate_updated_cards(
        model=model,
        current_memory=manager.memory_cards,
        conversation=conversation,
    )

    # 6. 同步更新到 JSON Cards。
    print("\n========== 记忆更新操作 ==========")

    sync_memory(
        manager=manager,
        cards=updated_cards,
        session_id=session_id,
    )

    # 7. 输出更新后的完整记忆。
    print("\n========== 本轮更新后的 JSON Cards ==========")
    print(manager.get_context_string())

    print(f"\n本轮会话：{session_id}")
    print(f"持久化文件：{STORAGE_PATH}")


if __name__ == "__main__":
    main()
