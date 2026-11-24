from typing import TYPE_CHECKING

from agent.context.context import AgentContext

if TYPE_CHECKING:
    from agent.context.context_manager import ContextManager


__all__=['AgentContext',
         'ContextManager',
         ]


def __getattr__(name: str):
    """按需加载上下文运行组件，避免配置模型导入时触发循环依赖。"""
    if name == "ContextManager":
        # ContextManager 依赖模型与 Token 统计，只在实际使用时导入。
        from agent.context.context_manager import ContextManager

        return ContextManager
    raise AttributeError(f"模块 {__name__!r} 没有属性 {name!r}")



