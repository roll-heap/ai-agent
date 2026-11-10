from dataclasses import dataclass

from agent.conversation import ConversationTurn

@dataclass
class SummarySegment:
    """
    保存整理后的摘要输入 表示一个连续历史区间
    SummaryInput
    ├── Segment 1
    │   └── R1
    │
    └── Segment 2
        ├── R3
        └── R4
    """
    start_index:int
    end_index:int
    # 保留原始索引，方便后续追踪来源
    turns: list[tuple[int, ConversationTurn]]

@dataclass
class SummaryInput:
    """
    完整的摘要输入 可以包含多个不连续区间
    SummaryInput
    ├── Segment 1
    │   └── R1
    │
    └── Segment 2
        ├── R3
        └── R4
    """
    segments:list[SummarySegment]