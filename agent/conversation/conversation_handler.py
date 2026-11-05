
from collections.abc import Callable, Sequence
from typing import Any

from agent.context import ContextManager
from agent.sesion.session import ConversationSession
from config import log

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
)


class ConversationHandler:
    """负责协调 Agent 的对话执行流程。"""

    def __init__(
        self,
        agent: Any,
        session: ConversationSession,
    ):
        self.agent = agent
        self.session = session

    async def run_agent_turn(
        self,
        question: str,
        on_text: Callable[[str], None],
    ) -> str:
        """执行一轮流式 Agent，并维护完整的对话消息状态。"""

        final_messages: Sequence[BaseMessage] | None = None

        seen_tool_calls: set[str] = set()
        seen_tool_results: set[str] = set()
        tool_names: dict[str, str] = {}

        history_message_count = len(self.session.history)

        # 1. 构建本轮上下文
        context = ContextManager.build_context(
            session=self.session,
            question=question,
        )
        request_messages = context.messages

        log.info(f"Agent 回合开始 | history_messages={history_message_count} "
                 f"| request_messages={len(request_messages)} | question={question}")

        # 2. 执行 Agent
        results = self.agent.astream(
            {"messages": request_messages},
            stream_mode=["messages", "values"],
            version="v2",
        )

        # 3. 处理流式事件
        async for part in results:
            mode = part["type"]
            payload = part["data"]

            if mode == "messages":
                message, _ = payload

                if isinstance(message.content, str) and message.content:
                    on_text(message.content)

            elif mode == "values" and "messages" in payload:
                final_messages = payload["messages"]

                log.info(f"Agent 状态快照 | {self._message_summary(final_messages)}")

                # 只处理本轮新增消息
                self._handle_tool_events(
                    final_messages[history_message_count:],
                    tool_names,
                    seen_tool_calls,
                    seen_tool_results,
                    on_text,
                )

        # 4. 检查 Agent 是否返回完整状态
        if final_messages is None:
            raise RuntimeError("Agent 未返回完整消息状态")

        # 5. 更新对话历史
        self._replace_history(final_messages)

        # 6. 提取最终回答
        final_answer = self._get_final_answer(final_messages)

        log.info(
            f"Agent 回合完成 | "
            f"history_messages={len(self.session.history)} | "
            f"final_answer={final_answer}"
        )

        return final_answer

    def _handle_tool_events(
        self,
        messages: Sequence[BaseMessage],
        tool_names: dict[str, str],
        seen_tool_calls: set[str],
        seen_tool_results: set[str],
        on_text: Callable[[str], None],
    ) -> None:
        """处理本轮新增的工具调用和工具返回事件。"""
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

    def _replace_history(self, messages: Sequence[BaseMessage]) -> None:
        """用 Agent 返回的完整消息状态替换跨轮历史。"""

        self.session.history[:] = messages

        log.info(f"Agent 历史已更新 | {self._message_summary(messages)}")


    def _get_final_answer(self, messages: Sequence[BaseMessage]) -> str:
        """提取最后一条非工具调用的 AI 回复。"""

        for message in reversed(messages):
            if isinstance(message, AIMessage) and not message.tool_calls:
                return message.text

        return ""

    def _message_summary(self, messages: Sequence[BaseMessage]) -> str:
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
