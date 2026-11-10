from agent.conversation.conversation_utils import ConversationUtils
from typing import TYPE_CHECKING
# 给开发工具看，主要是让 PyCharm、类型检查器知道 ConversationHandler 是什么
if TYPE_CHECKING:
    from agent.conversation.conversation_handler import ConversationHandler

__all__ = ['ConversationUtils','ConversationHandler']

# 解决运行时延迟导入问题，解决循环导入报错
def __getattr__(name: str) -> object:
    if name == 'ConversationHandler':
        from agent.conversation.conversation_handler import ConversationHandler
        return ConversationHandler
    raise AttributeError(f"module{__name__!r} has no attribute {name!r}")