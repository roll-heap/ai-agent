import pytest
from langchain_core.messages import AIMessage, HumanMessage
from agent.context.context_manager import ContextManager
from agent.context.model.summary_input import SummaryInput
from agent.conversation.model.conversation_turn import ConversationTurn


def make_turn(content: str) -> ConversationTurn:
    """创建完整对话轮次。"""
    return ConversationTurn(
        messages=[
            HumanMessage(content=content),
            AIMessage(content=f"回答：{content}"),
        ],
        is_complete=True,
    )


def test_build_summary_input_empty():
    """空候选列表应该返回空摘要输入。"""

    result = ContextManager.build_summary_input([])

    assert isinstance(result, SummaryInput)
    assert result.segments == []


def test_build_summary_input_single_turn():
    """单个轮次应该形成一个摘要区间。"""

    turn = make_turn("第一轮")

    result = ContextManager.build_summary_input([
        (0, turn),
    ])

    assert len(result.segments) == 1

    segment = result.segments[0]

    assert segment.start_index == 0
    assert segment.end_index == 0
    assert len(segment.turns) == 1
    assert segment.turns[0] == (0, turn)


def test_build_summary_input_continuous_turns():
    """连续轮次应该组织到同一个摘要区间。"""

    turns = [
        make_turn("第一轮"),
        make_turn("第二轮"),
        make_turn("第三轮"),
    ]

    result = ContextManager.build_summary_input([
        (0, turns[0]),
        (1, turns[1]),
        (2, turns[2]),
    ])

    assert len(result.segments) == 1

    segment = result.segments[0]

    assert segment.start_index == 0
    assert segment.end_index == 2
    assert [index for index, _ in segment.turns] == [0, 1, 2]


def test_build_summary_input_discontinuous_turns():
    """不连续轮次应该拆分成多个摘要区间。"""

    turns = [
        make_turn("第一轮"),
        make_turn("第三轮"),
        make_turn("第五轮"),
    ]

    result = ContextManager.build_summary_input([
        (0, turns[0]),
        (2, turns[1]),
        (4, turns[2]),
    ])

    assert len(result.segments) == 3

    assert [(segment.start_index, segment.end_index)for segment in result.segments] == [
        (0, 0),
        (2, 2),
        (4, 4),
    ]


def test_build_summary_input_out_of_order():
    """输入顺序混乱时，应该按照原始索引排序。"""

    turns = [
        make_turn("第一轮"),
        make_turn("第二轮"),
        make_turn("第三轮"),
    ]

    result = ContextManager.build_summary_input([
        (2, turns[2]),
        (0, turns[0]),
        (1, turns[1]),
    ])

    assert len(result.segments) == 1

    segment = result.segments[0]

    assert [index for index, _ in segment.turns] == [0, 1, 2]


def test_build_summary_input_does_not_modify_original_objects():
    """组织摘要输入不能修改原始轮次及其消息。"""

    turns = [
        make_turn("第一轮"),
        make_turn("第二轮"),
        make_turn("第三轮"),
    ]

    original_messages = [
        turn.messages.copy()
        for turn in turns
    ]

    original_states = [
        turn.is_complete
        for turn in turns
    ]

    result = ContextManager.build_summary_input([
        (0, turns[0]),
        (2, turns[2]),
        (1, turns[1]),
    ])

    # 原始消息列表没有变化
    for index, turn in enumerate(turns):
        assert turn.messages == original_messages[index]
        assert turn.is_complete == original_states[index]

    # 返回结果引用原始轮次对象，而不是创建副本
    for segment in result.segments:
        for _, turn in segment.turns:
            assert any(turn is original for original in turns)
