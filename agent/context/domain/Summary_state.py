from exception import AgentException


class SummaryState:
    """历史摘要状态"""
    # 当前有效摘要
    content: str=""
    # 摘要覆盖的完整历史轮次数量
    covered_turn_count: int = 0
    # 摘要版本
    version:int = 0

    def update(self, content: str, covered_turn_count: int) -> None:
        """提交新的摘要状态，调用之前必须已经成功生成摘要"""
        if not isinstance(content, str) or not content.strip():
            raise AgentException("摘要内容不能为空")
        if covered_turn_count < self.covered_turn_count:
            raise AgentException("摘要覆盖范围不能缩小")
        if covered_turn_count < 0:
            raise AgentException("摘要覆盖轮数不能小于0")
        self.content = content
        self.covered_turn_count = covered_turn_count
        self.version += 1