import asyncio
from typing import Any

from agent.sesion import Session
from agent.conversation import ConversationHandler
from config import trace

class AgentExecutor:
    def __init__(self, agent: Any):
        self.agent = agent
        self.handler = ConversationHandler(agent)

    @trace
    def execute(self, session: Session, question: str):
        try:
            async def stream_agent():
                print("\n🤖 正在思考...", flush=True)
                final_answer = await self.handler.run_agent_turn(
                    session,
                    question,
                    lambda text: print(text, end="", flush=True),
                )
                print()
                return final_answer

            return asyncio.run(stream_agent())
        except Exception:
            raise
