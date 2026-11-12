from collections.abc import Sequence

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage

from agent.history.conversation_turn import ConversationTurn
from exception import AgentException


class HistoryTurnParser:
    """负责将原始历史消息解析为结构化对话轮次"""
    SUPPORTED_MESSAGE_TYPES = (SystemMessage, HumanMessage, AIMessage, ToolMessage)

    def parse_turns(self, messages: Sequence[BaseMessage]) -> list[ConversationTurn]:
        """将原始消息序列解析为对话轮次
        轮次规则：
        1、HumanMessage 开始一个新轮次。
        2、AIMessage 和 ToolMessage 归属当前轮次。
        3、不存在待处理工具调用且协议有效时，AI 的无工具调用消息结束当前轮次。
        4、新 HumanMessage 到来时，尚未结束的上一轮标记为不完整。
        5、历史结束时，尚未结束的轮次标记为不完整。
        6、SystemMessage 不参与轮次划分。
        7、工具调用与工具结果通过 tool_call_id 关联。
        8、当前轮次发生协议异常后，不恢复协议有效状态。
        """
        turns: list[ConversationTurn] = []
        # 当前正在解析的轮次
        current_messages: list[BaseMessage] = []
        # 已发起但尚未收到结果的工具调用ID
        pending_tool_calls: set[str] = set()
        # 当前轮次中出现过的工具调用ID
        seen_tool_calls: set[str] = set()
        # 工具调用协议是否有效
        tool_protocol_valid = True

        def finish_turn(is_complete: bool) -> None:
            """保存当前轮次并重置解析状态"""
            nonlocal current_messages
            nonlocal pending_tool_calls
            nonlocal seen_tool_calls
            nonlocal tool_protocol_valid
            if current_messages:
                turns.append(ConversationTurn(messages=current_messages,is_complete=is_complete))
            # 开始下一轮前重置状态
            current_messages = []
            pending_tool_calls = set()
            seen_tool_calls = set()
            tool_protocol_valid = True

        for message in messages:
            # 显示抛异常，方便后续添加其他消息类型报错，便于发现
            if not isinstance(message, self.SUPPORTED_MESSAGE_TYPES):
                raise AgentException(f"不支持的消息类型：{type(message).__name__}")
            # 1、系统消息不属于对话轮次
            if isinstance(message, SystemMessage):
                continue
            # 2、HumanMessage开始新轮次
            if isinstance(message, HumanMessage):
                # 上一轮未正常结束
                if current_messages:
                    finish_turn(is_complete=False)
                current_messages.append(message)
                continue
            # 3、非用户消息必须属于一个已开始的轮次
            if not current_messages:
                raise AgentException(f"发现没有对应的HumanMessage的消息：{type(message).__name__}")
            # 4、处理AIMessage
            if isinstance(message, AIMessage):
                current_messages.append(message)
                # langChain无效工具调用
                if getattr(message, "invalid_tool_calls", None):
                    tool_protocol_valid = False
                tool_calls = message.tool_calls or []
                # 4.1 AI发起工具调用
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_call_id = tool_call.get("id")
                        # 工具调用必须有有效ID
                        if not isinstance(tool_call_id, str) or not tool_call_id:
                            tool_protocol_valid = False
                            continue
                        # 同一轮次内不允许重复的工具调用ID
                        if tool_call_id in seen_tool_calls:
                            tool_protocol_valid = False
                            continue
                        seen_tool_calls.add(tool_call_id)
                        pending_tool_calls.add(tool_call_id)
                    continue
                # 4,2 AI未发起工具调用，可能是最终回复
                if not pending_tool_calls and tool_protocol_valid:
                    finish_turn(is_complete=True)
                continue
            # 5、处理ToolMessage
            if isinstance(message, ToolMessage):
                current_messages.append(message)
                tool_call_id = message.tool_call_id
                # 工具结果必须具有有效ID
                if not isinstance(tool_call_id, str) or not tool_call_id:
                    tool_protocol_valid = False
                    continue
                # 必须存在对应的工具调用，且尚未收到过结果
                if tool_call_id not in pending_tool_calls:
                    tool_protocol_valid = False
                    continue
                # 工具调用得到对应的结果
                pending_tool_calls.remove(tool_call_id)
                continue
        # 7、保存历史末尾尚未完成的轮次
        if current_messages:
            finish_turn(is_complete=False)
        return turns
