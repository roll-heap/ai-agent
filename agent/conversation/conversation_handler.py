from collections.abc import Callable, Sequence
from typing import Any

from agent.context.context_manager import ContextManager
from agent.conversation.conversation_utils import ConversationUtils
from agent.sesion import Session
from config import log

from langchain_core.messages import BaseMessage, HumanMessage

from exception import AgentException


class ConversationHandler:
    """负责协调 Agent 的对话执行流程。"""

    def __init__(self, agent: Any):
        self.agent = agent

    async def run_agent_turn(self, session: Session, question: str, on_text: Callable[[str], None],
    ) -> str:
        """执行 Agent、处理工具事件、提取本轮新增消息并更新 Session。"""
        # 1. 构建本轮上下文
        context = ContextManager.build_context(
            session=session,
            question=question,
        )
        request_messages = context.messages
        if not request_messages:
            raise AgentException("本轮上下文不能为空")
        # 记录本轮实际发送的消息数量，因为未来 ContextManager 可能只选择部分历史消息。
        # 所以我们应该以 request_messages 为准，而不是以 session.history 为准。
        request_message_count = len(request_messages)
        log.info(f"Agent 回合开始 | request_message_count={request_message_count} "
                 f"| request_messages={len(request_messages)} | question={question}")
        # 当前用户消息
        current_user_message = request_messages[-1]
        if not isinstance(current_user_message, HumanMessage):
            raise AgentException("本轮上下文最后一条消息必须是 HumanMessage")

        # 执行 Agent
        try:
            final_messages = await self.run_agent(session, request_messages, on_text)
        except Exception:
            # 本轮执行失败只保存用户消息
            session.history.append(current_user_message)
            log.exception(f"Agent 执行失败，本轮只保存用户消息，history:{session.history}")
            raise

        # 执行成功，保存本轮完整消息
        new_messages = final_messages[request_message_count - 1:]
        # 提取最终回答
        final_answer = ConversationUtils.get_final_answer(final_messages)
        # 将本轮新增消息追加到完整会话历史。
        session.history.extend(new_messages)
        log.info(f"Agent 历史已追加 | 新增消息={len(new_messages)} | 历史消息总数={len(session.history)}")

        log.info(f"Agent 回合完成 | history_messages={len(session.history)} | final_answer={final_answer}")
        return final_answer


    async def run_agent(self, request_messages: Sequence[BaseMessage],
                        on_text: Callable[[str], None]
                        ) -> Sequence[BaseMessage]:
        final_messages: Sequence[BaseMessage] | None = None
        request_message_count = len(request_messages)
        tool_names: dict[str, str] = {}
        seen_tool_calls: set[str] = set()
        seen_tool_results: set[str] = set()
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
                log.info(f"Agent 状态快照 | {ConversationUtils.message_summary(final_messages)}")
                # 只处理本轮新增消息
                ConversationUtils.handle_tool_events(
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
        # 校验工具协议的完整性
        ConversationUtils.validate_tool_protocol(final_messages[request_message_count:])
        return final_messages