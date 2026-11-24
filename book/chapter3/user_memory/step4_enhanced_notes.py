# 本次实验使用统一的原始事实，确保两种格式的输入一致
from pathlib import Path

from book.chapter3.user_memory.simple_notes_memory_manager import SimpleNotesMemoryManager

SAMPLE_FACTS = [
    "用户在 A 公司担任 Java 架构师",
    "用户主要负责订单系统",
    "用户带领一支 8 人开发团队",
    "用户团队正在推进微服务改造",
    "用户比较喜欢使用 Spring Boot",
]
# Enhanced Notes 将上述相关事实组织成一段完整描述
ENHANCED_CONTENT = (
    "用户在 A 公司担任 Java 架构师，主要负责订单系统，"
    "带领一支 8 人开发团队，目前团队正在推进微服务改造。"
    "在技术选择方面，用户比较喜欢使用 Spring Boot。"
)
EXPERIMENT_TAG = "experiment_3_2"

def clean_experiment_data(manager: SimpleNotesMemoryManager) -> None:
    """
    清理当前实验之前生成的数据
    只删除带有本试验专属标签的记忆
    不影响同一个文件中其他未标记的记忆
    """
    experiment_notes=[note for note in manager.notes if EXPERIMENT_TAG in note.tags]
    for note in experiment_notes:
        manager.delete_memory(note.note_id)

def build_simple_note(manager:SimpleNotesMemoryManager) -> None:
    """
    将同一组事实拆分成多条独立记忆
    """
    clean_experiment_data(manager)
    for index, fact in enumerate(SAMPLE_FACTS, start=1):
        manager.add_memory(
            content=fact,
            session_id="session-simple",
            tags=[
                EXPERIMENT_TAG, f"fact_{index}"
            ]
        )

def build_enhanced_notes(manager:SimpleNotesMemoryManager) -> None:
    """
    将相关事实组织成一条完整的增强记忆
    """
    clean_experiment_data(manager)
    manager.add_memory(
        content=ENHANCED_CONTENT,
        session_id="session-enhanced",
        tags=[EXPERIMENT_TAG, "career", "team", "technology"]
    )

def calculate_content_length(manager:SimpleNotesMemoryManager) -> int:
    """
    统计本次实验记忆内容的总字符数
    """
    return sum(len(note.content) for note in manager.notes if EXPERIMENT_TAG in note.tags)

def print_experiment_result(name:str,manager:SimpleNotesMemoryManager) -> None:
    """
    输出当前记忆格式的实验结果
    """
    notes=[note for note in manager.notes if EXPERIMENT_TAG in note.tags]
    print(f"\n=========={name}==========")
    print(f"记忆数量：{len(notes)}")
    print((f"内容总字符数：{calculate_content_length(manager)}"))

    for index, note in enumerate(notes, start=1):
        print(f"{index}. {note.content}")

    # 使用相同关键词验证两种格式的基础文本检索
    search_result = manager.search_memories("订单系统")
    search_result = [note for note in search_result if EXPERIMENT_TAG in note.tags]
    print(f"关键词检索命中数量：{len(search_result)}")

def main() -> None:
    """
    执行SimpleNote与EnhancedNotes的初步对比实验
    """
    data_dir = Path(__file__).resolve().parent / "data"
    simple_path = data_dir / "simple_notes_test.json"
    enhanced_path = data_dir / "enhanced_notes_test.json"
    # 两个管理器服用同一个底层存储实现，但使用不同文件
    simple_manager = SimpleNotesMemoryManager(simple_path)
    enhanced_manager = SimpleNotesMemoryManager(enhanced_path)
    # 分别构建两种记忆组织形式
    build_simple_note(simple_manager)
    build_enhanced_notes(enhanced_manager)
    # 输出实验结果
    print_experiment_result("simple_notes", simple_manager)
    print_experiment_result("enhanced_notes", enhanced_manager)

if __name__=="__main__":
    main()