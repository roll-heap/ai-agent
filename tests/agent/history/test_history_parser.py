import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, ChatMessage, content

from agent.history import HistoryParser
from exception import AgentException


@pytest.fixture
def parser():
    return HistoryParser()

def make_tool_call(tool_call_id: str, name: str = "test_tool") -> dict:
    return {
        "name":name,
        "args":{},
        "id": tool_call_id,
        "type":"tool_call"
    }

# ==================== 普通对话 ====================
def test_single_turn(parser):
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好，有什么可以帮你？")
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True
    assert len(turns[0].messages) == 2

def test_multiple_turns(parser):
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好"),
        HumanMessage(content="今天天气怎么样？"),
        AIMessage(content="很好")
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 2
    assert all(turn.is_complete for turn in turns)

def test_system_message_ignored(parser):
    messages=[
        SystemMessage(content="系统提示词"),
        HumanMessage(content="你好"),
        SystemMessage(content="其他系统消息"),
        AIMessage(content="你好"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert len(turns[0].messages) == 2
    assert all(not isinstance(message, SystemMessage) for message in turns[0].messages)

# ==================== 工具调用 ====================
def test_single_tool_call(parser):
    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(content="工具调用", tool_calls=[make_tool_call("call_1")]),
        ToolMessage(content="晴天", tool_call_id="call_1"),
        AIMessage(content="今天是晴天"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True
    assert len(turns[0].messages) == 4


def test_multiple_tool_calls(parser):
    messages = [
        HumanMessage(content="查询天气和时间"),
        AIMessage(content="工具调用",tool_calls=[
                make_tool_call("call_1"),
                make_tool_call("call_2"),
            ]
        ),
        ToolMessage(content="天气晴朗", tool_call_id="call_1"),
        ToolMessage(content="12:00", tool_call_id="call_2"),
        AIMessage(content="天气晴朗，现在是12点"),
    ]

    turns = parser.parse_turns(messages)

    assert len(turns) == 1
    assert turns[0].is_complete is True


def test_tool_results_out_of_order(parser):
    messages = [
        HumanMessage(content="执行两个工具"),
        AIMessage(content="工具调用",tool_calls=[
                make_tool_call("call_1"),
                make_tool_call("call_2"),
            ]
        ),
        ToolMessage(content="结果2", tool_call_id="call_2"),
        ToolMessage(content="结果1", tool_call_id="call_1"),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True


# ==================== 不完整轮次 ====================

def test_missing_tool_result(parser):
    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(content='工具调用', tool_calls=[make_tool_call("call_1")]),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False


def test_duplicate_tool_call_id(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content="工具调用",tool_calls=[
                make_tool_call("call_1"),
                make_tool_call("call_1"),
            ]
        ),
        ToolMessage(content="结果", tool_call_id="call_1"),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False


def test_duplicate_tool_result(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content='工具调用', tool_calls=[make_tool_call("call_1")]),
        ToolMessage(content="结果", tool_call_id="call_1"),
        ToolMessage(content="重复结果", tool_call_id="call_1"),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False


def test_new_human_message_before_previous_turn_finished(parser):
    messages = [
        HumanMessage(content="第一轮"),
        AIMessage(content="工具调用", tool_calls=[make_tool_call("call_1")]),
        HumanMessage(content="第二轮"),
        AIMessage(content="第二轮回复"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 2
    assert turns[0].is_complete is False
    assert turns[1].is_complete is True


def test_history_ends_with_human_message(parser):
    messages = [
        HumanMessage(content="你好"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False


# ==================== 异常情况 ====================

def test_unsupported_message_type(parser):
    messages = [
        HumanMessage(content="你好"),
        ChatMessage(role="custom", content="不支持的消息"),
    ]

    with pytest.raises(AgentException, match="不支持的消息类型"):
        parser.parse_turns(messages)


@pytest.mark.parametrize(
    "message",
    [
        AIMessage(content="没有用户消息"),
        ToolMessage(content="没有用户消息", tool_call_id="call_1"),
    ],
)
def test_message_without_human_message(parser, message):
    with pytest.raises(AgentException):
        parser.parse_turns([message])

def test_invalid_tool_calls(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(
            content="",
            invalid_tool_calls=[
                {
                    "name": "test_tool",
                    "args": "{invalid json}",
                    "id": "call_1",
                    "error": "解析失败",
                    "type": "invalid_tool_call",
                }
            ],
        ),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False

def test_empty_tool_call_id(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content="工具调用",tool_calls=[make_tool_call("")]),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False

def test_empty_tool_result_id(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content="工具调用", tool_calls=[make_tool_call("call_1")]),
        ToolMessage(content="结果", tool_call_id=""),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False

def test_unknown_tool_result_id(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content='工具调用', tool_calls=[make_tool_call("call_1")]),
        ToolMessage(content="结果", tool_call_id="call_2"),
        AIMessage(content="执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False

def test_ai_reply_before_tool_result(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content="工具调用", tool_calls=[make_tool_call("call_1")]),
        AIMessage(content="工具还没返回，我先回复"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False

def test_tool_call_completed_before_ai_reply(parser):
    messages = [
        HumanMessage(content="执行工具"),
        AIMessage(content="工具调用", tool_calls=[make_tool_call("call_1")]),
        ToolMessage(content="执行成功", tool_call_id="call_1"),
        AIMessage(content="工具执行完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True

def test_overlapping_tool_call_batches(parser):
    messages = [
        HumanMessage(content="执行两个任务"),
        # 第一条 AIMessage 发起第一批工具调用
        AIMessage(content="", tool_calls=[make_tool_call("call_1")]),
        # 第一批尚未返回，第二条 AIMessage 又发起第二批
        AIMessage(content="", tool_calls=[make_tool_call("call_2")]),
        # 第一批工具结果返回
        ToolMessage(content="result_1", tool_call_id="call_1"),
        # 第二批工具结果返回
        ToolMessage(content="result_2", tool_call_id="call_2"),
        # AI 最终回复
        AIMessage(content="任务完成"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True
    assert turns[0].messages == messages

def test_tool_execution_error(parser):
    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(content='',tool_calls=[make_tool_call("call_1")]),
        ToolMessage(
            content="天气服务不可用",
            tool_call_id="call_1",
            status="error",
        ),
        AIMessage(content="天气服务暂时不可用"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True
    assert turns[0].messages == messages

def test_tool_result_after_final_answer(parser):
    messages = [
        HumanMessage(content="查询天气"),
        AIMessage(content='', tool_calls=[make_tool_call("call_1")]),
        AIMessage(content="查询完成"),
        ToolMessage(content="天气结果", tool_call_id="call_1"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False
    assert turns[0].messages == messages

def test_invalid_tool_protocol_cannot_be_recovered(parser):
    messages = [
        HumanMessage(content="查询天气"),
        # 出现异常：工具结果没有对应的工具调用
        ToolMessage(content="未知工具结果", tool_call_id="unknown_call"),
        # 后续正常发起工具调用
        AIMessage(content='', tool_calls=[make_tool_call("call_1")]),
        # 正常收到工具结果
        ToolMessage(content="上海晴天",tool_call_id="call_1",),
        # AI 正常给出最终回复
        AIMessage(content="上海今天晴天"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is False
    assert turns[0].messages == messages

def test_new_turn_resets_previous_turn_state(parser):
    messages = [
        # 第一轮开始
        HumanMessage(content="查询天气"),
        # 第一轮出现协议异常
        ToolMessage(content="未知工具结果",tool_call_id="unknown_call"),
        # 第二轮开始，第一轮被标记为不完整
        HumanMessage(content="现在几点了？"),
        # 第二轮正常结束
        AIMessage(content="现在是下午三点"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 2
    # 第一轮：协议异常，不完整
    assert turns[0].is_complete is False
    assert turns[0].messages == messages[:2]
    # 第二轮：正常结束，完整
    assert turns[1].is_complete is True
    assert turns[1].messages == messages[2:]

def test_consecutive_human_messages(parser):
    messages = [
        HumanMessage(content="第一个问题"),
        HumanMessage(content="第二个问题"),
        AIMessage(content="第二个问题的回答"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 2
    # 第一轮没有 AI 回复
    assert turns[0].is_complete is False
    assert turns[0].messages == messages[:1]
    # 第二轮正常结束
    assert turns[1].is_complete is True
    assert turns[1].messages == messages[1:]

def test_system_message_inside_turn_is_ignored(parser):
    messages = [
        HumanMessage(content="查询上海天气"),
        SystemMessage(content="系统提示信息"),
        AIMessage(content="上海今天晴天"),
    ]
    turns = parser.parse_turns(messages)
    assert len(turns) == 1
    assert turns[0].is_complete is True
    assert turns[0].messages == [messages[0], messages[2],
    ]