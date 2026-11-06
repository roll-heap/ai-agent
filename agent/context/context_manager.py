from langchain_core.messages import HumanMessage

from agent.context.context import AgentContext
from agent.sesion import Session


class ContextManager:
    @staticmethod
    def build_context(session: Session, question: str) -> AgentContext:
        """
        根据会话历史和当前问题构建本轮上下文
        """
        # messages = [*session.history,{"role": "user", "content": question}]
        # 上面的和本行两者都可以作为 LangChain 的消息输入。使用 HumanMessage 可以让我们统一使用 LangChain 消息对象
        messages = [*session.history, HumanMessage(content=question)]
        return AgentContext(messages)