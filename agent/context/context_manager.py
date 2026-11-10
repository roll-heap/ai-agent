from langchain_core.messages import HumanMessage
from langchain_core.messages.utils import count_tokens_approximately

from agent.context.context import AgentContext
from agent.context.model.summary_input import SummaryInput, SummarySegment
from agent.context.model.turn_classification import TurnClassification
from agent.conversation.conversation_utils import ConversationUtils
from agent.conversation.model.conversation_turn import ConversationTurn
from agent.sesion import Session
from exception import AgentException


class ContextManager:
    @staticmethod
    def classify_turns(turns: list[ConversationTurn],
                       recent_token_budget: int,
                       recent_max_turns: int) -> TurnClassification:
        """筛选近期轮次并分类"""
        if recent_token_budget < 0:
            raise AgentException("recent_token_budget不能小于0")
        if recent_max_turns < 0:
            raise AgentException("recent_max_turns不能小于0")
        # 1、找出末尾连续的不完整轮次  倒叙遍历
        recent_incomplete_indexes: set[int] = set()
        recent_complete_indexes: set[int] = set()
        # 发送给agent但不包括System prompt和工具定义等内容的tokens
        recent_tokens = 0
        # 发送给agent的轮次数
        recent_count = 0
        # 1、从后向前选择近期轮次
        for index in range(len(turns)-1, -1, -1):
            turn = turns[index]
            # 末尾连续不完整轮次整体保留
            if not turn.is_complete:
                if recent_count == 0:
                    recent_incomplete_indexes.add(index)
                    continue
                # 已经开始选择近期完整轮次，再遇到不完整轮次就停止
                break
            # 达到最大轮次，停止选择
            if recent_count >= recent_max_turns:
                break
            turn_tokens = count_tokens_approximately(turn.messages)
            # 超出预算，停止选择，不跳过当前轮次
            if recent_tokens + turn_tokens > recent_token_budget:
                break
            # 完整轮次
            recent_complete_indexes.add(index)
            recent_tokens += turn_tokens
            recent_count += 1
        # 3、分类
        recent_complete_turns = []
        summary_candidate_turns = []
        recent_incomplete_turns = []
        older_incomplete_messages = []
        for index, turn in enumerate(turns):
            if index in recent_complete_indexes:
                recent_complete_turns.append((index, turn))
            elif turn.is_complete:
                summary_candidate_turns.append((index, turn))
            elif index in recent_incomplete_indexes:
                recent_incomplete_turns.append((index, turn))
            else:
                # 较早不完整轮次只提取HumanMessage
                human_message = next((message for message in turn.messages if isinstance(message, HumanMessage)), None)
                if human_message is not None:
                    older_incomplete_messages.append((index, human_message))
        return TurnClassification(
            recent_complete_turn = recent_complete_turns,
            summary_candidate_turns = summary_candidate_turns,
            recent_incomplete_turns = recent_incomplete_turns,
            older_incomplete_message = older_incomplete_messages,
        )

    @staticmethod
    def build_summary_input(
            summary_candidate_turns:list[tuple[int, ConversationTurn]]
    ) -> SummaryInput:
        """按照原始顺序组织摘要后选轮次"""
        if not summary_candidate_turns:
            return SummaryInput(segments=[])
        # 按原始索引排序 对每个元素 item，取它的第 0 个位置的值作为排序键
        ordered_turns = sorted(summary_candidate_turns, key=lambda item: item[0])
        segments = []
        current_segment = []
        # 寻找连续的轮次作为一个批次
        for item in ordered_turns:
            if not current_segment:
                current_segment.append(item)
                continue
            pre_index = current_segment[-1][0]
            current_index = item[0]
            if current_index == pre_index + 1:
                current_segment.append(item)
            else:
                segments.append(SummarySegment(
                    start_index=current_segment[0][0],
                    end_index=current_segment[-1][0],
                    turns=current_segment
                ))
                current_segment = [item]
        # 保存最后一个区间
        if current_segment:
            segments.append(SummarySegment(
                start_index=current_segment[0][0],
                end_index=current_segment[-1][0],
                turns=current_segment
            ))
        return SummaryInput(segments=segments)





    @staticmethod
    def build_context(session: Session, question: str) -> AgentContext:
        """
        决定本轮 Agent 应该看到哪些信息。
        """
        # 拆分回话轮次
        turns = ConversationUtils.split_conversation_turns(session.history)
        messages = [message for turn in turns for message in turn.messages]
        messages.append(HumanMessage(content=question))
        return AgentContext(messages)