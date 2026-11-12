import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.context import ContextManager
from agent.history import HistoryTurnParser
from exception import AgentException


@pytest.fixture
def context_manager():
    return ContextManager(history_turn_parser=HistoryTurnParser())

def test_empty_history(context_manager):
    current_input = HumanMessage(content="你好")
    context = context_manager.build_context(history=[], current_input=current_input)
    assert context.messages == [current_input]

def test_multiple_complete_turns(context_manager):
    history = [
        HumanMessage(content="你好"),
        AIMessage(content="你好，有什么可以帮你？"),
        HumanMessage(content="介绍一下 Python"),
        AIMessage(content="Python 是一种编程语言。"),
    ]
    current_input = HumanMessage(content="什么是java")
    context = context_manager.build_context(history=history, current_input=current_input)
    # history.append(current_input)
    # assert context.messages == history
    assert context.messages == history + [current_input]

def test_incomplete_turn_is_preserved(context_manager):
    """不完整轮次原样保留。"""
    history = [HumanMessage(content="帮我查询天气"),]
    current_input = HumanMessage(content="继续")
    context = context_manager.build_context(history=history,current_input=current_input)
    assert context.messages == history + [current_input]


def test_invalid_current_input(context_manager):
    """当前输入不是 HumanMessage 时抛出异常。"""
    current_input = AIMessage(content="这不是用户输入")

    with pytest.raises(AgentException):
        context_manager.build_context(history=[],current_input=current_input,)


def test_original_history_is_not_modified(context_manager):
    """构建上下文不能修改原始历史。"""
    history = [HumanMessage(content="你好"),AIMessage(content="你好"),]
    original_history = history.copy()
    current_input = HumanMessage(content="再见")
    context_manager.build_context(history=history,current_input=current_input,)
    assert history == original_history

def test_incomplete_tool_call_turn_is_preserved(context_manager):
    """工具调用尚未返回结果时，保留不完整轮次的全部消息。"""
    history = [
        HumanMessage(content="帮我查询天气"),
        AIMessage(content="",tool_calls=[
                {
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "id": "call_001",
                    "type": "tool_call",
                }
            ],
        ),
    ]
    current_input = HumanMessage(content="继续")
    context = context_manager.build_context(history=history,current_input=current_input)
    assert context.messages == history + [current_input]

def test_complete_tool_call_turn_is_preserved(context_manager):
    """工具调用正常完成时，保留完整工具调用链及消息顺序。"""
    history = [
        HumanMessage(content="帮我查询天气"),
        AIMessage(content="",tool_calls=[
                {
                    "name": "query_weather",
                    "args": {"city": "北京"},
                    "id": "call_001",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(content="晴天，25℃",tool_call_id="call_001",),
        AIMessage(content="北京今天晴天，气温25℃。"),
    ]
    current_input = HumanMessage(content="谢谢")
    context = context_manager.build_context(history=history,current_input=current_input,)
    assert context.messages == history + [current_input]