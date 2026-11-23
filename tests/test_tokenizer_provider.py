"""Hugging Face tokenizer 消息转换的回归测试。"""

import unittest

from langchain_core.messages import AIMessage

from agent.context.token_count.provider.tokenizer_provider import TokenizerProvider


class TokenizerProviderTest(unittest.TestCase):
    """验证消息转换结果与 Qwen chat template 的输入契约一致。"""

    def test_tool_call_arguments_remain_a_mapping(self) -> None:
        """Qwen 模板通过 `items` 遍历工具调用参数。"""
        # LangChain 标准化后的工具参数是字典，必须保持映射类型。
        message = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "weather_tool",
                    "args": {"city": "上海"},
                    "id": "call-1",
                }
            ],
        )

        converted = TokenizerProvider._convert_messages([message])

        self.assertEqual(
            converted[0]["tool_calls"][0]["function"]["arguments"],
            {"city": "上海"},
        )


if __name__ == "__main__":
    unittest.main()
