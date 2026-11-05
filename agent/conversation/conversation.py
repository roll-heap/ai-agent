from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages import ToolMessage

from config import log


def replace_history(history: list, messages: Sequence[BaseMessage]) -> None:
    """用 Agent 返回的完整消息状态替换跨轮历史。"""
    history[:] = messages
    log.info(f"Agent 历史已更新 | {_message_summary(messages)}")


async def run_agent_turn(
    agent: Any,
    history: list,
    question: str,
    on_text: Callable[[str], None],
) -> str:
    """执行一轮流式 Agent，并保留工具调用协议需要的全部消息。"""
    final_messages: Sequence[BaseMessage] | None = None
    seen_tool_calls: set[str] = set()
    seen_tool_results: set[str] = set()
    tool_names: dict[str, str] = {}
    history_message_count = len(history)
    request_messages = [*history, {"role": "user", "content": question}]
    log.info(
        f"Agent 回合开始 | history_messages={len(history)} | "
        f"request_messages={len(request_messages)} | question={question}"
    )

    async for part in agent.astream(
        {"messages": request_messages},
        stream_mode=["messages", "values"],
        version="v2",
    ):
        mode = part["type"]
        payload = part["data"]
        if mode == "messages":
            message, _ = payload
            if isinstance(message.content, str) and message.content:
                on_text(message.content)
        elif mode == "values" and "messages" in payload:
            final_messages = payload["messages"]
            log.info(f"Agent 状态快照 | {_message_summary(final_messages)}")
            # Agent 状态包含历史消息；只展示本轮新增的工具事件。
            for message in final_messages[history_message_count:]:
                if isinstance(message, AIMessage):
                    for tool_call in message.tool_calls:
                        tool_call_id = tool_call.get("id")
                        tool_name = tool_call["name"]
                        if tool_call_id:
                            tool_names[tool_call_id] = tool_name
                        call_key = tool_call_id or f"{tool_name}:{tool_call['args']!r}"
                        if call_key not in seen_tool_calls:
                            on_text(
                                f"\n🔧 调用工具：{tool_name}\n"
                                f"   参数：{tool_call['args']}\n"
                            )
                            seen_tool_calls.add(call_key)
                elif isinstance(message, ToolMessage):
                    tool_call_id = message.tool_call_id
                    result_key = tool_call_id or f"{message.name}:{message.text}"
                    if result_key not in seen_tool_results:
                        tool_name = tool_names.get(
                            tool_call_id,
                            message.name or "unknown_tool",
                        )
                        on_text(
                            f"\n✅ 工具返回（{tool_name}）：{message.text}\n"
                        )
                        seen_tool_results.add(result_key)

    if final_messages is None:
        raise RuntimeError("Agent 未返回完整消息状态")

    replace_history(history, final_messages)
    final_answer = _get_final_answer(final_messages)
    log.info(
        f"Agent 回合完成 | history_messages={len(history)} | "
        f"final_answer={final_answer}"
    )
    return final_answer


def _get_final_answer(messages: Sequence[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.text
    return ""


def _message_summary(messages: Sequence[BaseMessage]) -> str:
    """返回用于排障的完整消息协议详情。"""
    summary = []
    for index, message in enumerate(messages):
        if isinstance(message, AIMessage):
            tool_calls = [
                {
                    "name": tool_call["name"],
                    "id": tool_call["id"],
                    "args": tool_call["args"],
                }
                for tool_call in message.tool_calls
            ]
            summary.append(
                f"{index}:ai(content={message.text!r}, tool_calls={tool_calls})"
            )
        elif isinstance(message, ToolMessage):
            summary.append(
                f"{index}:tool(name={message.name}, tool_call_id={message.tool_call_id}, "
                f"content={message.text!r})"
            )
        else:
            summary.append(f"{index}:{message.type}(content={message.text!r})")
    return " | ".join(summary)
