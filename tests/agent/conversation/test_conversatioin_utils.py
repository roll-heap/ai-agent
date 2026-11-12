import pytest

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from agent.conversation.conversation_utils import ConversationUtils
from exception import AgentException


def test_empty_messages():
    """空消息列表应该返回空轮次列表"""

    result = ConversationUtils.split_conversation_turns([])

    assert result == []


def test_normal_conversation():
    """正常的 HumanMessage + AIMessage 应该组成完整轮次"""

    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好，有什么可以帮助你？"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 1

    turn = result[0]

    assert turn.messages == messages
    assert turn.is_complete is True
    assert turn.protocol_valid is True
    assert turn.has_pending_tool_calls is False
    assert turn.protocol_errors == []


def test_pending_tool_call():
    """工具调用尚未返回时，协议有效但轮次不完整"""

    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                }
            ],
        ),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.is_complete is False
    assert turn.protocol_valid is True
    assert turn.has_pending_tool_calls is True
    assert turn.protocol_errors == []


def test_tool_call_with_result_without_final_ai():
    """工具返回后没有最终 AI 回复，协议有效但轮次不完整"""

    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content="晴天",
            tool_call_id="call_001",
        ),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.is_complete is False
    assert turn.protocol_valid is True
    assert turn.has_pending_tool_calls is False
    assert turn.protocol_errors == []


def test_multiple_tool_calls():
    """一个 AIMessage 可以同时发起多个工具调用"""

    messages = [
        HumanMessage(content="查询天气和时间"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                },
                {
                    "id": "call_002",
                    "name": "current_time",
                    "args": {},
                    "type": "tool_call",
                },
            ],
        ),
        ToolMessage(
            content="晴天",
            tool_call_id="call_001",
        ),
        ToolMessage(
            content="12:00",
            tool_call_id="call_002",
        ),
        AIMessage(content="北京天气晴朗，现在是12点。"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.is_complete is True
    assert turn.protocol_valid is True
    assert turn.has_pending_tool_calls is False


def test_tool_message_without_matching_call():
    """ToolMessage 没有对应的工具调用时，协议无效"""

    messages = [
        HumanMessage(content="查询天气"),
        ToolMessage(
            content="晴天",
            tool_call_id="call_001",
        ),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.is_complete is False
    assert turn.protocol_valid is False
    assert turn.has_pending_tool_calls is False
    assert len(turn.protocol_errors) == 1


def test_duplicate_tool_call_id():
    """同一轮次中不能重复使用 tool_call_id"""

    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content="晴天",
            tool_call_id="call_001",
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "上海"},
                    "type": "tool_call",
                }
            ],
        ),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.protocol_valid is False
    assert any(
        "tool_call_id 重复" in error
        for error in turn.protocol_errors
    )


def test_final_ai_with_pending_tool_call():
    """工具尚未返回时不能直接生成最终回复"""

    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="北京天气晴朗"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    turn = result[0]

    assert turn.is_complete is False
    assert turn.protocol_valid is False
    assert turn.has_pending_tool_calls is True


def test_multiple_incomplete_turns():
    """多个不完整轮次都应该保留，不能只提取其中一个"""

    messages = [
        HumanMessage(content="第一个问题"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_001",
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "type": "tool_call",
                }
            ],
        ),
        HumanMessage(content="第二个问题"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_002",
                    "name": "query_weather",
                    "args": {"city": "上海"},
                    "type": "tool_call",
                }
            ],
        ),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 2

    assert result[0].is_complete is False
    assert result[0].has_pending_tool_calls is True

    assert result[1].is_complete is False
    assert result[1].has_pending_tool_calls is True


def test_multiple_human_messages():
    """新的 HumanMessage 应该开始新的轮次"""

    messages = [
        HumanMessage(content="第一个问题"),
        AIMessage(content="第一个回答"),
        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个回答"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 2

    assert result[0].is_complete is True
    assert result[1].is_complete is True


def test_history_must_start_with_human_message():
    """AIMessage 或 ToolMessage 不能作为历史的第一条消息"""

    messages = [
        AIMessage(content="你好"),
    ]

    with pytest.raises(
        AgentException,
        match="历史消息必须以HumanMessage开始",
    ):
        ConversationUtils.split_conversation_turns(messages)


def test_system_message_is_not_supported():
    """SystemMessage 不属于当前历史消息支持的类型"""

    messages = [
        HumanMessage(content="你好"),
        SystemMessage(content="你是一个助手"),
    ]

    with pytest.raises(
        AgentException,
        match="不支持的消息类型：SystemMessage",
    ):
        ConversationUtils.split_conversation_turns(messages)


def test_system_message_as_first_message():
    """SystemMessage 即使位于第一条，也应该报告不支持的类型"""

    messages = [
        SystemMessage(content="你是一个助手"),
    ]

    with pytest.raises(
        AgentException,
        match="不支持的消息类型：SystemMessage",
    ):
        ConversationUtils.split_conversation_turns(messages)