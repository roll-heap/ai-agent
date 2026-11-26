"""OpenRouter 示例的密钥配置回归测试。"""

import ast
import unittest
from pathlib import Path


OPENROUTER_EXAMPLE_PATHS = (
    Path("book/chapter3/user_memory/step12_openrouter_function_calling.py"),
    Path("book/chapter3/user_memory/step13_openrouter_react_memory_agent.py"),
)


class OpenRouterApiKeyConfigTest(unittest.TestCase):
    """确保示例不会在源码中保存 OpenRouter API Key。"""

    def test_api_key_is_read_from_environment(self) -> None:
        """每个 OpenRouter 示例都应从 OPENROUTER_API_KEY 环境变量读取密钥。"""
        for example_path in OPENROUTER_EXAMPLE_PATHS:
            module = ast.parse(example_path.read_text(encoding="utf-8"))
            assignment_value = next(
                node.value
                for node in module.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "OPENROUTER_API_KEY"
                    for target in node.targets
                )
            )

            self.assertIsInstance(assignment_value, ast.Call, example_path)
            self.assertIsInstance(assignment_value.func, ast.Attribute, example_path)
            self.assertIsInstance(assignment_value.func.value, ast.Name, example_path)
            self.assertEqual(assignment_value.func.value.id, "os", example_path)
            self.assertEqual(assignment_value.func.attr, "getenv", example_path)
            self.assertEqual(len(assignment_value.args), 1, example_path)
            self.assertIsInstance(assignment_value.args[0], ast.Constant, example_path)
            self.assertEqual(
                assignment_value.args[0].value,
                "OPENROUTER_API_KEY",
                example_path,
            )


if __name__ == "__main__":
    unittest.main()
