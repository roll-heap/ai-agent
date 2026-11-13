import asyncio
from typing import Any

from langchain_core.messages import HumanMessage

from agent.context import ContextManager
from agent.session import Session
from agent.conversation import ConversationHandler
from config import trace


class AgentExecutor:
    def __init__(self, agent: Any, context_manager: ContextManager):
        self.agent = agent
        self.handler = ConversationHandler(agent=agent)
        self.context_manager = context_manager

    @trace
    def execute(self, session: Session, question: str):
        # 1. 构建本轮上下文
        current_user_message = HumanMessage(content=question)
        context = self.context_manager.build_context(
            history=session.history,
            current_input=current_user_message,
        )
        request_messages = context.messages

        async def stream_agent():
            print("\n🤖 正在思考...", flush=True)
            final_answer = await self.handler.run_agent_turn(
                session,
                request_messages,
                lambda text: print(text, end="", flush=True),
            )
            print()
            return final_answer

        return asyncio.run(stream_agent())
