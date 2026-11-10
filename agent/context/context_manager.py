from langchain_core.messages import HumanMessage

from agent.context.context import AgentContext
from agent.conversation.conversation_utils import ConversationUtils
from agent.sesion import Session


class ContextManager:
    @staticmethod
    def build_context(session: Session, question: str) -> AgentContext:
        """
        决定本轮 Agent 应该看到哪些信息。
        """
        turns = ConversationUtils.split_conversation_turns(session.history)
        messages = [message for turn in turns for message in turn.messages]
        messages.append(HumanMessage(content=question))
        return AgentContext(messages)