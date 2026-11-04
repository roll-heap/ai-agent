import asyncio
import unittest

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

from agent.conversation.conversation import run_agent_turn


class V2StreamAgent:
    async def astream(self, *args, **kwargs):
        answer = AIMessage(content="上海今天晴。")
        yield {
            "type": "messages",
            "ns": (),
            "data": (AIMessageChunk(content="上海今天晴。"), {}),
        }
        yield {
            "type": "values",
            "ns": (),
            "data": {"messages": [HumanMessage(content="今天上海天气"), answer]},
        }


class ToolStreamAgent:
    async def astream(self, *args, **kwargs):
        human_message = HumanMessage(content="今天上海天气")
        tool_call = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "weather_tool",
                    "args": {"city": "上海"},
                    "id": "call_weather_1",
                    "type": "tool_call",
                }
            ],
        )
        tool_result = ToolMessage(
            content='{"temperature": "20°C"}',
            name="weather_tool",
            tool_call_id="call_weather_1",
        )
        answer = AIMessage(content="上海当前 20°C。")

        yield {
            "type": "values",
            "ns": (),
            "data": {"messages": [human_message, tool_call]},
        }
        yield {
            "type": "values",
            "ns": (),
            "data": {"messages": [human_message, tool_call, tool_result]},
        }
        yield {
            "type": "values",
            "ns": (),
            "data": {"messages": [human_message, tool_call, tool_result, answer]},
        }


class ConversationTests(unittest.TestCase):
    def test_run_agent_turn_reads_v2_stream_parts(self):
        history = []
        streamed_text = []

        answer = asyncio.run(
            run_agent_turn(
                V2StreamAgent(),
                history,
                "今天上海天气",
                streamed_text.append,
            )
        )

        self.assertEqual(answer, "上海今天晴。")
        self.assertEqual(streamed_text, ["上海今天晴。"])
        self.assertEqual(len(history), 2)

    def test_run_agent_turn_streams_tool_name_and_result_once(self):
        output = []

        asyncio.run(
            run_agent_turn(
                ToolStreamAgent(),
                [],
                "今天上海天气",
                output.append,
            )
        )

        printed = "".join(output)
        self.assertIn("调用工具：weather_tool", printed)
        self.assertIn("参数：{'city': '上海'}", printed)
        self.assertIn('工具返回（weather_tool）：{"temperature": "20°C"}', printed)
        self.assertEqual(printed.count("调用工具：weather_tool"), 1)
        self.assertEqual(printed.count("工具返回（weather_tool）"), 1)


if __name__ == "__main__":
    unittest.main()
