class SummeryState:
    """历史摘要状态"""
    # 当前有效摘要
    content: str=""
    # 摘要覆盖的完整历史轮次数量
    covered_turn_count: int = 0
    # 摘要版本
    version:int = 0