"""摘要管理器模块边界的回归测试。"""

import ast
import unittest
from pathlib import Path

from langchain_core.messages import ToolMessage

from agent.context.summary.summary_manager import SummaryManager


class SummaryManagerModuleTest(unittest.TestCase):
    """确保摘要模块只声明类型，不在导入时创建运行时对象。"""

    def test_module_has_no_runtime_assignments(self) -> None:
        """模块导入不能触发摘要模型初始化或异步调用。"""
        # 读取源码并检查模块级节点，避免测试本身导入被测模块后触发副作用。
        module_path = Path("agent/context/summary/summary_manager.py")
        module = ast.parse(module_path.read_text(encoding="utf-8"))
        runtime_assignments = [
            node
            for node in module.body
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        ]

        self.assertEqual(runtime_assignments, [])

    def test_serializes_tool_message_with_complete_role_label(self) -> None:
        """工具消息应保留工具名、内容和关联调用 ID。"""
        # 该方法不依赖实例状态，绕过模型初始化以保持单元测试确定性。
        manager = SummaryManager.__new__(SummaryManager)
        message = ToolMessage(content="晴天", name="天气", tool_call_id="call-1")

        result = manager._serialize_message(message)

        self.assertEqual(result, "工具结果（天气）:晴天\n工具调用ID：call-1")


if __name__ == "__main__":
    unittest.main()
