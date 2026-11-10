from dataclasses import dataclass

from agent.conversation import ConversationTurn

@dataclass
class TurnClassification:
    """对话轮次分类结果"""
    # 被选中的近期完整轮次 (原始索引, ConversationTurn)
    recent_complete_turn: list[tuple[int, ConversationTurn]]
    # 可以参与摘要的较早完整轮次 (原始索引, ConversationTurn)
    summary_candidate_turns: list[tuple[int, ConversationTurn]]
    # 可以参与摘要的较早完整轮次 (原始索引, ConversationTurn)
    recent_incomplete_turns: list[tuple[int, ConversationTurn]]
    # 较早不完整轮次中提取的 HumanMessage (原始索引, HumanMessage)
    older_incomplete_message: list[tuple[int, ConversationTurn]]
