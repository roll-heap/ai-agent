
"""
实验 3-2：验证 JSON Cards 在后续对话中的读取和使用

实验目标：
1. 从持久化文件重新加载 JSON Cards。
2. 验证之前生成的用户偏好确实存在。
3. 将记忆上下文提供给模型。
4. 提出一个与偏好相关的问题。
5. 提出一个与偏好无关的问题。
6. 观察模型是否正确使用记忆，以及是否错误套用记忆。

注意：
本实验复用现有 JSON Cards 管理器，不实现新的检索算法。
"""

from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage

from book.chapter3.user_memory.json_card_memory_manager import (
    JsonCardsMemoryManager,
)
from book.chapter3.user_memory.step8_json_card_generation import (
    init_chat_model,
    extract_text,
    STORAGE_PATH,
)


# ============================================================
# 一、实验问题
# ============================================================

# 相关问题：回答中包含数值，适合观察单位偏好是否生效。
RELEVANT_QUESTION = "地球到月球的平均距离大约是多少？"

# 无关问题：不涉及数值单位偏好，观察模型是否错误套用记忆。
UNRELATED_QUESTION = "请用通俗语言解释什么是光合作用。"


# ============================================================
# 二、加载并检查记忆
# ============================================================

def load_memory_manager() -> JsonCardsMemoryManager:
    """
    重新实例化管理器，从持久化文件加载已有记忆。
    """
    if not STORAGE_PATH.exists():
        raise FileNotFoundError(
            f"记忆文件不存在，请先运行 step8 实验：{STORAGE_PATH}"
        )

    # 构造管理器时会自动调用 load_memory()。
    manager = JsonCardsMemoryManager(STORAGE_PATH)

    if not manager.memory_cards:
        raise RuntimeError("持久化文件中没有可用的记忆卡片")

    return manager


def verify_preference_memory(
    manager: JsonCardsMemoryManager,
) -> None:
    """
    检查之前生成的数值单位偏好是否成功恢复。
    """
    results = manager.search_memories("单位")

    if not results:
        raise RuntimeError("没有检索到数值单位偏好记忆")

    print("\n========== 持久化记忆检查 ==========")

    for memory_path, memory_data in results:
        print(f"记忆 ID：{memory_path}")
        print(f"记忆内容：{memory_data.get('value')}")
        print(f"记忆来源：{memory_data.get('source')}")


# ============================================================
# 三、使用记忆回答问题
# ============================================================

def answer_with_memory(
    model,
    memory_context: str,
    question: str,
    question_type: str,
) -> None:
    """
    将已保存的记忆作为上下文提供给模型，并回答当前问题。

    每个问题独立调用模型，避免前一个问题的回答影响后一个问题。
    """
    system_prompt = f"""
你是一个能够使用用户长期记忆的助手。

下面是从持久化存储中读取的用户记忆：

<memory>
{memory_context}
</memory>

回答要求：
1. 只有当记忆与当前问题相关时，才使用对应记忆。
2. 不要为了套用记忆而改变无关问题的回答。
3. 如果记忆中存在用户明确表达的回答偏好，应在适用场景中遵循。
4. 不要编造记忆中不存在的用户事实。
"""

    response = model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    )

    answer = extract_text(response.content)

    print(f"\n========== {question_type} ==========")
    print(f"用户问题：{question}")
    print(f"模型回答：\n{answer}")


# ============================================================
# 四、实验入口
# ============================================================

def main() -> None:
    # 1. 重新加载持久化记忆。
    manager = load_memory_manager()

    # 2. 验证目标偏好已经恢复。
    verify_preference_memory(manager)

    # 3. 获取当前全部记忆上下文。
    memory_context = manager.get_context_string()

    print("\n========== 提供给模型的记忆上下文 ==========")
    print(memory_context)

    # 4. 初始化模型，复用 step8 的模型配置。
    model = init_chat_model()

    # 5. 测试相关问题。
    answer_with_memory(
        model=model,
        memory_context=memory_context,
        question=RELEVANT_QUESTION,
        question_type="相关问题测试",
    )

    # 6. 测试无关问题。
    answer_with_memory(
        model=model,
        memory_context=memory_context,
        question=UNRELATED_QUESTION,
        question_type="无关问题测试",
    )


if __name__ == "__main__":
    main()
