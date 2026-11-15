import asyncio

from langchain_core.messages import HumanMessage

from agent.context import ContextManager
from agent.factory import AgentFactory
from agent.profile import AgentProfile
from agent.session import Session
from agent.conversation import ConversationHandler
from config import trace, log
from exception import AgentException


class AgentExecutor:
    def __init__(self, agent_factory: AgentFactory, context_manager: ContextManager):
        self.agent_factory = agent_factory
        self.context_manager = context_manager
        self.handler = ConversationHandler()

    @trace
    def execute(self, session: Session, question: str, profile: AgentProfile):
        if not question or not question.strip():
            raise AgentException("用户问题不能为空")
        # 1.创建当前轮用户消息
        current_user_message = HumanMessage(content=question)
        # 2、根据 AgentProfile 获取本轮运行Agent的配置
        runtime_config = self.agent_factory.get_agent_runtime_config(
            model_config=profile.model_config,
            connection_config=profile.connection_config,
            system_prompt=profile.system_prompt,
            agent_tools=profile.tools
        )
        # 3、构建当前 Agent 所需上下文
        context = self.context_manager.build_context(
            history=session.history,
            current_input=current_user_message,
            runtime_config=runtime_config
        )
        request_messages = context.messages
        # 4. 执行当前 Agent
        async def stream_agent():
            print("\n🤖 正在思考...", flush=True)
            final_answer = await self.handler.run_agent_turn(
                runtime_config=runtime_config,
                session=session,
                request_messages=request_messages,
                on_text=lambda text: print(text, end="", flush=True),
            )
            print()
            return final_answer

        try:
            return asyncio.run(stream_agent())
        except Exception as e:
            log.exception(f"agent执行异常：{e}")
            pass
