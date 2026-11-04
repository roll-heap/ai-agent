import uuid
from datetime import datetime

from logcore import set_correlation_id

from config import Logger, log
from web.config.base_model import ChatRequest, ChatResponse
from web.config.session_manager import session_manager


class AgentService:
    """agent 业务服务"""
    def __init__(self, agent):
        self.agent = agent

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """处理对话请求，支持多轮对话"""
        # 异步添加trace_id
        trace_id = Logger.set_trace_id()

        session_id = request.session_id or str(uuid.uuid4())
        history = session_manager.get_history(session_id)

        log.info(f"session={session_id[:8]} | {request.question[:50]}...")
        try:
            # 1、追加用户消息
            history.append({"role":"user", "content":request.question})

            # 2、调用agent
            start_time = datetime.now()
            result = self.agent.invoke({"messages": history})
            answer = result["messages"][-1].content
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # 追加AI回复
            history.append({"role":"assistant", "content":answer})

            log.info(f"回复成功 ｜ 耗时：{elapsed_ms:.2f}")
            return ChatResponse(
                answer=answer,
                session_id=session_id,
                trace_id=trace_id,
                elapsed_ms=elapsed_ms
            )
        except Exception as e:
            log.exception("处理失败，准备回退消息")
            if history and history[-1]["role"] == "user":
                history.pop()
            raise
        finally:
            set_correlation_id(None)