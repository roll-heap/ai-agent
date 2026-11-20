from collections.abc import Callable, Sequence
from typing import Any

from agent.init import AgentRuntimeConfig
from agent.session import Session
from config import log
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from exception import AgentException


class ConversationHandler:
    """负责协调 Agent 的对话执行流程。"""

    async def run_agent_turn(
            self,
            runtime_config: AgentRuntimeConfig,
            session: Session,
            request_messages: list[BaseMessage],
            on_text: Callable[[str], None],
    ) -> str:
        """执行 Agent、处理工具事件、提取本轮新增消息并更新 Session。"""
        if not request_messages:
            raise AgentException("本轮上下文不能为空")
        current_user_message = request_messages[-1]
        if not isinstance(current_user_message, HumanMessage):
            raise AgentException("本轮上下文最后一条消息必须是HumanMessage")
        request_message_count = len(request_messages)
        log.info(f"Agent 回合开始 | request_messages_count={request_message_count} | question={current_user_message}")
        # 执行 Agent
        try:
            final_messages = await self.run_agent(
                agent=runtime_config.agent,
                request_messages=request_messages,
                on_text=on_text
            )
        except Exception as e:
            # 本轮执行失败只保存用户消息
            session.append_messages(current_user_message)
            log.exception(f"Agent 执行失败，本轮只保存用户消息，history:{session.history},{e}")
            raise

        # 执行成功，保存本轮完整消息
        new_messages = final_messages[request_message_count - 1:]
        # 提取最终回答
        final_answer = self.get_final_answer(final_messages)
        # 将本轮新增消息追加到完整会话历史。
        session.append_messages(new_messages)
        log.info(f"Agent 历史已追加 | 新增消息={len(new_messages)} | 历史消息总数={len(session.history)}")

        log.info(f"Agent 回合完成 | history_messages={len(session.history)} | final_answer={final_answer}")
        return final_answer


    async def run_agent(
            self,
            agent: Any,
            request_messages: Sequence[BaseMessage],
            on_text: Callable[[str], None]
    ) -> Sequence[BaseMessage]:
        final_messages: Sequence[BaseMessage] | None = None
        request_message_count = len(request_messages)
        tool_names: dict[str, str] = {}
        seen_tool_calls: set[str] = set()
        seen_tool_results: set[str] = set()
        results = agent.astream(
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
                log.info(f"Agent 状态快照 | {self.message_summary(final_messages)}")
                # 只处理本轮新增消息
                self.handle_tool_events(
                    final_messages[request_message_count:],
                    tool_names,
                    seen_tool_calls,
                    seen_tool_results,
                    on_text,
                )
        # 4. 检查 Agent 是否返回完整状态
        if final_messages is None:
            raise AgentException("Agent 未返回完整消息状态")
        # 前缀一致性校验，如果某个 Middleware 修改、删除或重排了输入消息，程序就不会悄悄地按照错误索引保存历史
        if final_messages[:request_message_count] != request_messages:
            raise AgentException("Agent 返回的消息状态与请求消息前缀不一致")
        return final_messages

    @staticmethod
    def handle_tool_events(
            messages: Sequence[BaseMessage],
            tool_names: dict[str, str],
            seen_tool_calls: set[str],
            seen_tool_results: set[str],
            on_text: Callable[[str], None],
    ) -> None:
        """
        处理本轮新增的工具调用和工具返回事件。
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
                    tool_name = tool_names.get(tool_call_id, message.name or "unknown_tool", )
                    on_text(f"\n✅ 工具返回（{tool_name}）: {message.text}\n")

                    seen_tool_results.add(result_key)

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
            elif isinstance(message, HumanMessage):
                summary.append(
                    f"{index}:human("
                    f"content={message.text!r})"
                )
            else:
                summary.append(
                    f"{index}:{message.type}"
                    f"(content={message.text!r})"
                )

        return " | ".join(summary)