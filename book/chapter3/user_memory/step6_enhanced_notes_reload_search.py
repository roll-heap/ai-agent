"""
实验3-2:Enhanced Notes持久化重载与多角度检索
验证目标：
1、新建MemoryManager时，能否自动从Json恢复记忆
2、能否通过不同关键词检索到Enhanced Notes
3、理解当前关键词检索的能力边界
"""
from pathlib import Path

from book.chapter3.user_memory.simple_notes_memory_manager import SimpleNotesMemoryManager


def main()-> None:
    """
    执行持久化重载与多角度检索实验
    """
    # 定位之前LLM生成实验使用的持久化文件
    storage_path = Path(__file__).resolve().parent / "data" / "enhanced_notes_llm_test.json"
    # 创建全新的记忆管理器实例
    # 构造函数内部会自动调用 load_memory()
    manager = SimpleNotesMemoryManager(storage_path)
    # 验证是否成功恢复记忆
    print("========== 持久化重载验证 ==========")
    print(f"加载文件：{storage_path}")
    print(f"加载记忆数量：{len(manager.notes)}")
    for note in manager.notes:
        print(f"记忆ID：{note.note_id}")
        print(f"记忆内容：{note.content}")
        print(f"记忆标签：{note.tags}")
    # # 从不同信息纬度进行关键词检索
    # test_queries = [
    #     "A 公司",       # 公司信息
    #     "Java 架构师",  # 职业与职位
    #     "订单系统",     # 业务职责
    #     "8 人",         # 团队规模
    #     "微服务改造",   # 团队工作
    #     "Spring Boot",  # 技术偏好
    # ]
    # 测试语义相近、但不包含原文关键词的查询
    test_queries = [
        "用户负责什么业务？",
        "用户目前担任什么职位？",
        "他管理多少名员工？",
        "团队现在正在开展什么工作？",
        "用户在技术选型方面有什么倾向？",
    ]
    print("\n========== 多角度检索验证 ==========")
    for query in test_queries:
        results = manager.search_memories(query)

        print(f"\n检索关键词：{query}")
        print(f"匹配数量：{len(results)}")

        for note in results:
            print(f"匹配记忆：{note.content}")

if __name__=="__main__":
    main()