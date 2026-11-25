
"""
实验 3-2：Enhanced Notes 多轮订阅记忆更新

本实验使用项目已有的原始 YAML 测试数据，
逐轮将新对话整合到已有的自然语言记忆中。

本轮先只运行 Netflix（第 1 轮），后续轮次待验收后再执行。
python -m book.chapter3.user_memory.step7_enhanced_notes_subscription_update --session-index 1
python -m book.chapter3.user_memory.step7_enhanced_notes_subscription_update --session-index 2
python -m book.chapter3.user_memory.step7_enhanced_notes_subscription_update --session-index 3
"""

import argparse
from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import HumanMessage, SystemMessage

from book.chapter3.user_memory.simple_notes_memory_manager import (
    SimpleNotesMemoryManager,
)
from book.chapter3.user_memory.step5_enhanced_notes_generation import (
    init_chat_model,
    format_conversation,
    extract_text,
)


# ============================================================
# 一、实验文件路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# 直接读取项目已有的原始测试数据，不复制、不修改。
TEST_CASE_PATH = (
    BASE_DIR
    / "test_cases"
    / "layer2"
    / "04_multiple_subscriptions.yaml"
)

# 使用独立持久化文件，避免覆盖之前的偏好实验数据。
STORAGE_PATH = BASE_DIR / "data" / "enhanced_notes_subscription_test.json"

# 本次实验专属标签，用于识别实验记忆。
EXPERIMENT_TAG = "experiment_3_2_subscription"


# ============================================================
# 二、记忆更新 Prompt
# ============================================================

SYSTEM_PROMPT = """
你是一个用户长期记忆整理助手。

你的任务是根据已有记忆和用户的新对话，
生成一份更新后的完整自然语言记忆。

请遵守以下规则：

1. 保留已有记忆中仍然有效的信息。
2. 将新对话中明确表达或能够可靠确认的信息整合进去。
3. 如果新信息明确纠正旧信息，以新信息为准。
4. 不允许无依据地推测或编造事实。
5. 保留重要的主体、时间、金额和事实关联。
6. 区分当前实际订阅方案与仅作为备选讨论的方案。
7. 不要遗漏仍然有效的旧订阅信息。
8. 使用第三人称，以自然、完整的中文段落输出。
9. 不要输出标题、解释、分析过程或 Markdown 格式。

只输出更新后的完整记忆内容。
"""


# ============================================================
# 三、读取原始测试用例
# ============================================================

def load_test_case() -> dict[str, Any]:
    """读取原始 YAML 测试数据。"""

    if not TEST_CASE_PATH.exists():
        raise FileNotFoundError(
            f"找不到测试用例文件：{TEST_CASE_PATH}"
        )

    with TEST_CASE_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("测试用例根节点必须是字典")

    histories = data.get("conversation_histories")

    if not isinstance(histories, list) or len(histories) != 3:
        raise ValueError("订阅案例必须包含三段原始对话")

    return data


# ============================================================
# 四、生成更新后的 Enhanced Note
# ============================================================

def generate_updated_note(
    model: Any,
    previous_memory: str | None,
    messages: list[dict[str, str]],
) -> str:
    """
    根据已有记忆和当前对话生成完整的新记忆。

    第一轮 previous_memory 为空；
    后续轮次传入上一轮保存的完整记忆。
    """

    conversation = format_conversation(messages)

    if not conversation.strip():
        raise ValueError("当前对话内容不能为空")

    if previous_memory:
        memory_text = previous_memory
    else:
        memory_text = "当前没有已有记忆。"

    human_prompt = f"""
请根据以下已有记忆和本轮对话，生成更新后的完整用户记忆。

<previous_memory>
{memory_text}
</previous_memory>

<new_conversation>
{conversation}
</new_conversation>
"""

    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ])

    updated_memory = extract_text(response.content)

    if not updated_memory:
        raise ValueError("模型返回的更新记忆为空")

    return updated_memory


# ============================================================
# 五、执行单轮实验
# ============================================================

def run_session(
    session_index: int,
    model: Any,
    manager: SimpleNotesMemoryManager,
    histories: list[dict[str, Any]],
) -> None:
    """执行指定轮次的记忆更新。"""

    if session_index < 1 or session_index > 3:
        raise ValueError("session_index 必须在 1 到 3 之间")

    current_session = histories[session_index - 1]
    session_id = current_session["conversation_id"]
    messages = current_session["messages"]

    # 避免同一轮重复执行，造成实验状态不明确。
    if any(
        note.session_id == session_id
        for note in manager.notes
    ):
        raise ValueError(
            f"本轮对话已经执行过：{session_id}。"
            "请勿直接重复执行。"
        )

    # 第一轮必须从空记忆开始。
    if session_index == 1 and manager.notes:
        raise ValueError(
            "第一轮实验要求使用空记忆文件，请检查实验数据。"
        )

    # 后续轮次必须建立在上一轮的记忆基础上。
    if session_index > 1 and len(manager.notes) != 1:
        raise ValueError(
            "后续轮次要求持久化文件中存在且仅存在一条实验记忆。"
        )

    previous_memory = None
    memory_id = None

    if manager.notes:
        previous_memory = manager.notes[0].content
        memory_id = manager.notes[0].note_id

    # 调用 LLM 生成完整更新后的自然语言记忆。
    updated_memory = generate_updated_note(
        model=model,
        previous_memory=previous_memory,
        messages=messages,
    )

    # 第一轮新增，后续轮次更新同一条记忆。
    if memory_id is None:
        memory_id = manager.add_memory(
            content=updated_memory,
            session_id=session_id,
            tags=[EXPERIMENT_TAG],
        )
        operation = "新增记忆"
    else:
        success = manager.update_memory(
            memory_id=memory_id,
            content=updated_memory,
            session_id=session_id,
            tags=[EXPERIMENT_TAG],
        )

        if not success:
            raise RuntimeError("更新已有记忆失败")

        operation = "更新已有记忆"

    print("\n========== Enhanced Notes 订阅更新实验 ==========")
    print(f"实验轮次：{session_index}")
    print(f"对话 ID：{session_id}")
    print(f"执行操作：{operation}")
    print(f"记忆 ID：{memory_id}")
    print("\n更新后的完整记忆：")
    print(updated_memory)
    print(f"\n当前记忆数量：{len(manager.notes)}")
    print(f"持久化文件：{STORAGE_PATH}")


# ============================================================
# 六、实验入口
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhanced Notes 多轮订阅记忆更新实验"
    )

    parser.add_argument(
        "--session-index",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="指定实验轮次：1=Netflix，2=Disney+，3=Max",
    )

    args = parser.parse_args()

    # 读取书中原始案例数据。
    test_case = load_test_case()

    # 初始化项目已有模型。
    model = init_chat_model()

    # 初始化现有记忆管理器。
    manager = SimpleNotesMemoryManager(STORAGE_PATH)

    # 执行指定轮次。
    run_session(
        session_index=args.session_index,
        model=model,
        manager=manager,
        histories=test_case["conversation_histories"],
    )


if __name__ == "__main__":
    main()
