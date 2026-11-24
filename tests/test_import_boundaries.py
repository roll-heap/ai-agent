"""模块导入边界的回归测试。"""

import subprocess
import sys
import unittest


class ImportBoundaryTest(unittest.TestCase):
    """验证模型配置与上下文运行组件不会在导入阶段循环依赖。"""

    def test_model_config_can_be_imported_in_a_clean_python_process(self) -> None:
        """模型配置依赖上下文配置类型时，仍应能独立完成导入。"""
        result = subprocess.run(
            [sys.executable, "-c", "from agent.model import ModelConfig"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_context_manager_remains_available_from_context_package(self) -> None:
        """延迟导出后，既有的包级 ContextManager 导入方式必须保持可用。"""
        from agent.context import ContextManager

        self.assertEqual(ContextManager.__name__, "ContextManager")


if __name__ == "__main__":
    unittest.main()
