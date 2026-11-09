import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from agent.conversation.conversation_utils import ConversationUtils
from exception import AgentException


def test_empty_message():
    """空消息列表应该返回空轮次列表"""
    result = ConversationUtils.split_conversation_turns([])
    assert result == []
    print("test_empty_message", result)


def test_human_message_and_ai_message():
    """正常的HumanMessage + AIMessage 应该组成一轮完整对话"""
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好，有什么可以帮你？"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert  len(result) == 1
    assert  result[0].messages == messages
    assert  result[0].is_complete is True


def test_tool_message_is_supported():
    """ToolMessage是支持的消息类型，可以进入当前轮次"""
    messages = [
        HumanMessage(content="查询天气"),
        ToolMessage(content="小雨", tool_call_id="call_001"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    # 当前ToolMessage没有对应的AI工具调用
    # 属于协议异常，但不应该出发消息类型异常
    assert result[0].is_complete is False

@pytest.mark.parametrize(
    "message",
    [
        pytest.param(
            AIMessage(content="你好"),
            id="ai_message-first",
        ),
        pytest.param(
            ToolMessage(
                content="工具结果",
                tool_call_id='call_001',
            ),
            id = 'tool-message_first',
        ),
    ],
)
def test_history_must_start_with_human_message(message):
    """AIMessage 或 ToolMessage 不能作为历史的第一条消息"""
    with pytest.raises(
        AgentException,
        match="历史消息必须以HumanMessage开始",
    ):
        ConversationUtils.split_conversation_turns([message])

def test_system_message_is_not_supported():
    """systemMessage不属于当前历史支持的类型"""
    messages = [
        HumanMessage(content="你好"),
        SystemMessage(content="你是一个助手"),
    ]
    with pytest.raises(
        AgentException,
        match="不支持的消息类型：SystemMessage",
    ):
        ConversationUtils.split_conversation_turns(messages)

def test_unsupported_messgae_type_as_first_message():
    """第一条消息是SystemMessage时，应明确报告不支持的类型"""
    messages = [
        SystemMessage(content="你是一个助手"),
    ]
    with pytest.raises(
        AgentException,
        match="不支持的消息类型：SystemMessage",
    ):
        ConversationUtils.split_conversation_turns(messages)


def test_tool_result_requires_final_ai_after_tool_response():
    """工具结果返回后，必须有新的AI最终会的，轮次才能完整"""
    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name":"query_weather",
                    "args":{"city":"北京"},
                    "id":"call_001",
                    "type":"tool_call",
                }
            ],
        ),
        AIMessage(content="天气查询中，请稍等"),
        ToolMessage(
            content="晴天",
            tool_call_id="call_001",
        ),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].is_complete is False


def test_consecutive_tool_calls_form_one_complete_turn():
    """
    连续两次工具调用及最终回答应该组成一个完整轮次
    HumanMessage
        ↓
    AIMessage(tool_calls: call_001)
        ↓
    ToolMessage(call_001)
        ↓
    AIMessage(tool_calls: call_002)
        ↓
    ToolMessage(call_002)
        ↓
    AIMessage(final_answer)
    """
    messages = [
        HumanMessage(content="查询北京天气，并计算20+30"),
        # 第一次工具调用：查询天气
        AIMessage(
            content="",
            tool_calls=[{
                "name":"query_weather",
                "args":{"city":"北京"},
                "id":"call_001",
                "type":"tool_call",
            }],
        ),
        ToolMessage(
            content="北京天气晴朗",
            tool_call_id="call_001",
        ),
        # 第二次工具调用：计算
        AIMessage(
            content="",
            tool_calls=[{
                "name":"calculater",
                "args":{"expression":"20+30"},
                "id":"call_002",
                "type":"tool_call",
            }],
        ),
        ToolMessage(
            content="20+30=50",
            tool_call_id="call_002",
        ),
        # 最终回答
        AIMessage(content="北京天气晴朗，20+30=50"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is True

def test_parallel_tool_calls_with_out_of_order_results():
    """
    并行工具调用的结果乱序返回，仍应组成一个完整轮次
    HumanMessage
        ↓
    AIMessage(tool_calls: call_001, call_002)
        ↓
    ToolMessage(call_002)  ← 第二个工具先返回
        ↓
    ToolMessage(call_001)  ← 第一个工具后返回
        ↓
    AIMessage(final_answer)
    """
    messages = [
        HumanMessage(content="查询北京天气，并计算20+30"),
        # 一次AIMessage同时发起两个工具调用
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name":"query_weather",
                    "args":{"city":"北京"},
                    "id":"call_001",
                    "type":"tool_call",
                },
                {
                    "name":"calculater",
                    "args":{"expression":"20+30"},
                    "id":"call_002",
                    "type":"tool_call",
                },
            ],
        ),
        # 第二个工具先返回
        ToolMessage(
            content="20+30=50",
            tool_call_id="call_002",
        ),
        # 第一个工具后返回
        ToolMessage(
            content="北京天气晴朗",
            tool_call_id="call_001",
        ),
        AIMessage(content="北京天气晴朗，20+30=50")
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is True

def test_duplicate_tool_call_ids_in_one_ai_message():
    """
    同一条AIMessage中存在重复工具调用ID,轮次应该不完整
    HumanMessage
        ↓
    AIMessage(
        tool_calls=[
            call_001,
            call_001  ← 重复 ID
        ]
    )
        ↓
    ToolMessage(call_001)
        ↓
    AIMessage(final_answer)
    """
    messages = [
        HumanMessage(content="查询北京天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name":"query_weather",
                    "args":{"city":"北京"},
                    "id":"call_001",
                    "type":"tool_call",
                },{
                    "name":"query_weather",
                    "args": {"city": "上海"},
                    "id": "call_001",
                    "type": "tool_call",
                }
            ]
        ),
        ToolMessage(
            content="北京天气晴朗",
            tool_call_id="call_001",
        ),
        AIMessage(content="天气查询完成"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is False

def test_duplicate_tool_messages_with_same_tool_call_id():
    """
    同一个工具调用ID收到两条ToolMessage,轮次应该不完整
    HumanMessage
        ↓
    AIMessage(tool_calls: call_001)
        ↓
    ToolMessage(call_001)  ← 第一次返回
        ↓
    ToolMessage(call_001)  ← 重复返回
        ↓
    AIMessage(final_answer)
    预期结果：
        - 只有一个对话轮次。
        - 包含全部 5 条消息。
        - is_complete is False。
        - 重复的工具结果不能被当作合法结果。
    """
    messages = [
        HumanMessage(content="查询北京天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name":"query_weather",
                    "args":{"city":"北京"},
                    "id":"call_001",
                    "type":"tool_call",
                }
            ],
        ),
        # 第一次工具结果
        ToolMessage(
            content="北京天气晴朗",
            tool_call_id="call_001",
        ),
        # 重复的工具结果
        ToolMessage(
            content="北京天气多云",
            tool_call_id="call_001",
        ),
        AIMessage(content="北京天气查询完成"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is False


def test_tool_message_with_unknown_tool_call_id():
    """
    ToolMessage 的 ID 不存在于待处理工具调用集合中，轮次应该不完整
    HumanMessage
        ↓
    AIMessage(tool_calls: call_001)
        ↓
    ToolMessage(call_002)  ← 没有对应的工具调用
        ↓
    AIMessage(final_answer)
    """

    messages = [
        HumanMessage(content="查询北京天气"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "id": "call_001",
                    "type": "tool_call",
                }
            ],
        ),
        # 返回了一个没有对应工具调用的结果
        ToolMessage(
            content="上海天气晴朗",
            tool_call_id="call_002",
        ),
        AIMessage(content="天气查询完成"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is False

def test_consecutive_human_messages_start_new_turn():
    """
    连续的 HumanMessage 应开启新轮次，前一轮标记为不完整
    按照我们确定的轮次规则：
        - 一轮从 HumanMessage 开始。
        - 遇到下一个 HumanMessage，意味着上一轮结束。
        - 如果上一轮只有 HumanMessage，没有最终 AI 回复，则 is_complete=False。
        - 新的 HumanMessage 应开启一个全新的轮次，不受上一轮状态影响。
    """
    messages = [
        HumanMessage(content="第一个问题"),
        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个问题的回答"),
    ]
    result = ConversationUtils.split_conversation_turns(messages)
    assert len(result) == 2
    # 第一轮只有 HumanMessage，因此不完整
    assert result[0].messages == [
        HumanMessage(content="第一个问题")
    ]
    assert result[0].is_complete is False
    # 第二轮包含 HumanMessage 和最终 AIMessage，因此完整
    assert result[1].messages == [
        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个问题的回答"),
    ]
    assert result[1].is_complete is True

def test_complete_turn_followed_by_incomplete_turn():
    """完整轮次后追加未完成轮次，两轮状态应独立"""

    messages = [
        HumanMessage(content="第一个问题"),
        AIMessage(content="第一个问题的回答"),

        HumanMessage(content="第二个问题"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 2

    # 第一轮完整
    assert result[0].is_complete is True
    assert result[0].messages == messages[:2]

    # 第二轮只有 HumanMessage，不完整
    assert result[1].is_complete is False
    assert result[1].messages == messages[2:]

def test_multiple_complete_turns():
    """多个连续完整轮次应正确划分，消息不能遗漏或错位"""

    messages = [
        HumanMessage(content="第一个问题"),
        AIMessage(content="第一个回答"),

        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个回答"),

        HumanMessage(content="第三个问题"),
        AIMessage(content="第三个回答"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 3

    for index, turn in enumerate(result):
        assert turn.is_complete is True
        assert turn.messages == messages[index * 2:index * 2 + 2]

    # 所有轮次重新拼接后，应与原始消息完全一致
    reconstructed_messages = [
        message
        for turn in result
        for message in turn.messages
    ]
    assert reconstructed_messages == messages

def test_final_ai_is_reset_when_new_tool_call_appears():
    """
    验证 AI 已经给出普通回答，随后又发起工具调用
    普通 AI 回复之后再次发起工具调用，应重新等待最终回答
    HumanMessage
        ↓
    AIMessage（普通回答）
        ↓
    AIMessage（发起工具调用 call_001）
        ↓
    ToolMessage（返回 call_001 的结果）
        ↓
    AIMessage（最终回答）
    """

    messages = [
        HumanMessage(content="查询北京天气"),
        AIMessage(content="我先确认一下天气信息"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "id": "call_001",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content="北京天气晴朗",
            tool_call_id="call_001",
        ),
        AIMessage(content="北京今天晴朗"),
    ]

    result = ConversationUtils.split_conversation_turns(messages)

    assert len(result) == 1
    assert result[0].messages == messages
    assert result[0].is_complete is True