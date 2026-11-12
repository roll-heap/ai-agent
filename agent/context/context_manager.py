from langchain_core.messages import HumanMessage, BaseMessage

from agent.context.context import AgentContext
from agent.sesion import Session

class ContextManager:
    @staticmethod
    def build_context(session: Session, question: str) -> AgentContext:
        """
        决定本轮 Agent 应该看到哪些信息。
        """
        messages = [*session.history, HumanMessage(content=question)]
        return AgentContext(messages)