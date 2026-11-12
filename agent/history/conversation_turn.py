from dataclasses import dataclass

from langchain_core.messages import BaseMessage


@dataclass
class ConversationTurn:
    """一轮对话
    正常完成的轮次
        messages: 1. HumanMessage：用户提出问题
                 2. AIMessage：发起工具调用
                 3. ToolMessage：工具返回结果
                 4. AIMessage：最终回复
        is_complete = True
    异常中断的轮次
        messages:
            1. HumanMessage：用户提出问题
            2. AIMessage：发起工具调用
            3. ToolMessage：工具尚未返回
        is_complete = False
    """
    # 保存该轮次的原始消息
    messages: list[BaseMessage]
    # 标记该轮次是否正常结束
    # （Session 保存的是原始消息历史，程序可能在 Agent 执行期间发生异常或中断，导致历史中存在尚未完成的轮次）
    is_complete: bool