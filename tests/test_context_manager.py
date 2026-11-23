"""上下文管理器的消息角色回归测试。"""

import unittest
from types import SimpleNamespace

from langchain_core.messages import HumanMessage, SystemMessage

from agent.context.context_manager import ContextManager
from agent.context.domain import ContextBudgetConfig
from agent.context.token_count import TokenCountResult


class RecordingTokenCounter:
    """记录 Token 统计输入，避免测试依赖真实 tokenizer。"""

    def __init__(self) -> None:
        self.messages = []

    def count(self, **kwargs) -> TokenCountResult:
        """返回一个始终满足上下文预算的固定统计结果。"""
        self.messages = kwargs["messages"]
        return TokenCountResult(total_tokens=1)


class ContextManagerTest(unittest.TestCase):
    """验证摘要在模型消息序列中的角色。"""

    def test_summary_is_not_added_as_a_second_system_message(self) -> None:
        """模型的静态系统提示词后不能出现第二条 system 消息。"""
        # 使用轻量替身隔离 Token 统计与摘要模型，专注验证消息编排。
        token_counter = RecordingTokenCounter()
        manager = ContextManager(
            history_turn_parser=SimpleNamespace(),
            token_counter=token_counter,
            budget_config=ContextBudgetConfig(safety_base_tokens=0, safety_ratio=0),
            summary_manager=SimpleNamespace(),
        )
        runtime_config = SimpleNamespace(
            system_prompt="系统提示词",
            model_config=SimpleNamespace(context_window=100, max_output_tokens=1),
            connection_config=SimpleNamespace(),
            tools=(),
        )

        result = manager._select_history(
            candidate_turns=[],
            current_input=HumanMessage(content="当前问题"),
            runtime_config=runtime_config,
            summary_content="此前任务已经完成。",
        )

        self.assertIsInstance(result.messages[0], HumanMessage)
        self.assertIn("历史摘要", result.messages[0].content)
        self.assertEqual(
            sum(isinstance(message, SystemMessage) for message in token_counter.messages),
            1,
        )


if __name__ == "__main__":
    unittest.main()
