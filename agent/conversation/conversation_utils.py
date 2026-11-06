from collections.abc import Callable, Sequence
from agent.sesion import Session
from config import log
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from exception import AgentException


class ConversationUtils:
    """
    会话处理工具类，处理agent交互过程中的对话
    """

    @staticmethod
    def handle_tool_events(
        messages: Sequence[BaseMessage],
        tool_names: dict[str, str],
        seen_tool_calls: set[str],
        seen_tool_results: set[str],
        on_text: Callable[[str], None],
    ) -> None:
        """
        识别 AIMessage 中的工具调用。
        记录 tool_call_id 与工具名称的关系。
        识别 ToolMessage 并展示工具结果。
        """
        for message in messages:
            if isinstance(message, AIMessage):
                for tool_call in message.tool_calls:
                    tool_call_id = tool_call.get("id")
                    tool_name = tool_call["name"]

                    if tool_call_id:
                        tool_names[tool_call_id] = tool_name

                    call_key = (
                        tool_call_id
                        or f"{tool_name}:{tool_call['args']!r}"
                    )

                    if call_key not in seen_tool_calls:
                        on_text(f"\n🔧 调用工具：{tool_name} 参数：{tool_call['args']}\n")
                        seen_tool_calls.add(call_key)

            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                result_key = (tool_call_id or f"{message.name}:{message.text}")
                if result_key not in seen_tool_results:
                    tool_name = tool_names.get(tool_call_id, message.name or "unknown_tool",)
                    on_text(f"\n✅ 工具返回（{tool_name}）: {message.text}\n")

                    seen_tool_results.add(result_key)

    @staticmethod
    def append_history(session: Session, messages: Sequence[BaseMessage]) -> None:
        """将本轮新增消息追加到完整会话历史。"""
        session.history.extend(messages)
        log.info(f"Agent 历史已追加 | 新增消息={len(messages)} | 历史消息总数={len(session.history)}")

    @staticmethod
    def get_final_answer(messages: Sequence[BaseMessage]) -> str:
        """提取最后一条非工具调用的 AI 回复。"""

        for message in reversed(messages):
            if isinstance(message, AIMessage) and not message.tool_calls:
                return message.text

        return ""

    @staticmethod
    def message_summary(messages: Sequence[BaseMessage]) -> str:
        """生成用于排障的完整消息协议详情。"""
        summary = []
        for index, message in enumerate(messages):

            if isinstance(message, AIMessage):
                tool_calls = [
                    {
                        "name": call["name"],
                        "id": call["id"],
                        "args": call["args"],
                    }
                    for call in message.tool_calls
                ]

                summary.append(
                    f"{index}:ai("
                    f"content={message.text!r}, "
                    f"tool_calls={tool_calls})"
                )

            elif isinstance(message, ToolMessage):
                summary.append(
                    f"{index}:tool("
                    f"name={message.name}, "
                    f"tool_call_id={message.tool_call_id}, "
                    f"content={message.text!r})"
                )

            else:
                summary.append(
                    f"{index}:{message.type}"
                    f"(content={message.text!r})"
                )

        return " | ".join(summary)

    @staticmethod
    def validate_tool_protocol(messages: Sequence[BaseMessage]) -> None:
        """
        校验本轮工具调用与工具返回是否完整匹配。
            规则	                                说明
        调用 ID 唯一	            同一回合不能重复出现相同的工具调用 ID
        返回必须有对应调用	        ToolMessage 的 tool_call_id 必须能找到对应的 AIMessage 工具调用
        每次调用必须有返回	        每个工具调用 ID 都必须存在对应的 ToolMessage
        通过： AIMessage: call_001 ToolMessage: call_001
        不通过：AIMessage: call_001 ToolMessage: call_002
        不通过：AIMessage: call_001 ToolMessage: （缺失）
        """
        # 检查工具调用是否重复
        tool_call_ids = set()
        # 检查工具返回是否重复。
        tool_result_ids = set()
        for message in messages:
            # 收集AI发起的工具调用
            if isinstance(message, AIMessage):
                # 校验tool_call_id的有效性
                for tool_message in message.tool_calls:
                    tool_call_id = tool_message.get("id")
                    if not tool_call_id:
                        raise AgentException("工具调用缺少有效的tool_call_id")
                    if tool_call_id in tool_call_ids:
                        raise AgentException(f"发现重复的工具调用ID:{tool_call_id}")
                    tool_call_ids.add(tool_call_id)
            # 收集工具返回
            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                if not tool_call_id:
                    raise AgentException("工具返回缺少有效的tool_call_id")
                if tool_call_id in tool_result_ids:
                    raise AgentException(f"发现重复的工具返回ID:{tool_call_id}")
                tool_result_ids.add(tool_call_id)
        # 检查是否存在未返回的工具调用  集合差集
        missing_result = tool_call_ids - tool_result_ids
        # 检查是否存在没有对应调用的工具返回  集合差集
        orphan_results = tool_result_ids - tool_call_ids
        if missing_result or orphan_results:
            raise AgentException(f"工具调用协议不完整 ｜ 缺少返回:{missing_result} | 缺少调用:{orphan_results}")
