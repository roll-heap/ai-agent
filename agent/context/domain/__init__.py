from typing import TYPE_CHECKING

from agent.context.domain.Summary_state import SummaryState
from agent.context.domain.context_budget_config import ContextBudgetConfig
from agent.context.domain.hugging_face_config import HuggingFaceConfig
from agent.context.domain.input_modality import InputModality

if TYPE_CHECKING:
    from agent.context.domain.history_selection_result import HistorySelectionResult



__all__=[
    "InputModality",
    "HuggingFaceConfig",
    "HistorySelectionResult",
    "ContextBudgetConfig",
    "SummaryState"
]


def __getattr__(name: str):
    """按需加载依赖 Token 统计的领域结果，保持包级导入兼容。"""
    if name == "HistorySelectionResult":
        # 避免 ModelConfig 仅获取 HuggingFaceConfig 时加载 Token 统计链。
        from agent.context.domain.history_selection_result import HistorySelectionResult

        return HistorySelectionResult
    raise AttributeError(f"模块 {__name__!r} 没有属性 {name!r}")
