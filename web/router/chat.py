from fastapi import Depends, HTTPException, APIRouter, Body, Request

from web.config.base_model import ChatResponse, ChatRequest
from web.service.agent_service import AgentService

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["对话"],
    # dependencies=[Depends(verify_token)]  # 公共依赖（如认证）
)

# 依赖函数的参数名改为 req（明确它是 Request 对象）
def get_agent(req:Request): # 类型提示为 Request
    """依赖注入：获取 Agent 实例"""
    return req.app.state.agent

@router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest= Body(...),  # ✅ 改为 chat_request，避免冲突
            agent=Depends(get_agent)
):
    """
    对话入口
    - 支持多轮对话：传入 session_id 可保证上下文
    - 不传 session_id 会自动生成新会话
    :param request:
    :param agent:
    :return:
    """
    try:
        service = AgentService(agent)
        return await service.process_chat(chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e.__context__))