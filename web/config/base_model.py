from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=500)
    session_id: Optional[str] = Field(default=None, description="会话ID,用户多轮对话")

class ChatResponse(BaseModel):
    """对话响应"""
    answer: str
    session_id: str
    trace_id: str
    elapsed_ms: float