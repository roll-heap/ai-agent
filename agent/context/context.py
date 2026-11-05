from dataclasses import dataclass
from langchain_core.messages import BaseMessage


@dataclass
class AgentContext:
    """
    它负责封装本轮准备交给 Agent 的初始消息
    以后可以扩展：
        数据	                来源	                        用途
        历史消息	    ConversationSession	            保持对话连续性
        当前问题	            用户输入	                明确本轮任务
        检索文档	            向量数据库	            补充外部知识
        系统提示词	        Agent 配置	            约束模型行为
        Token 统计	        Context Manager	        控制上下文预算
        工具结果	            Agent 执行过程	        支持后续模型调用
    """
    messages:list[BaseMessage]