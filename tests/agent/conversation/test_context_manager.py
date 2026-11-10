from langchain_core.messages import AIMessage,HumanMessage,ToolMessage

from agent.context import ContextManager
from agent.sesion import Session


class TestContextManager:
    """ContextManager 集成测试"""

    @staticmethod
    def create_session(history=None) -> Session:
        """创建测试会话"""
        session = Session()
        session.history = history or []
        return session

    @staticmethod
    def create_complete_tool_turn() -> list:
        """创建一个完整的工具调用轮次"""
        return [
            HumanMessage(content="北京天气怎么样？"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_weather",
                        "args": {"city": "北京"},
                        "id": "call_001",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content="晴天",
                tool_call_id="call_001",
            ),
            AIMessage(content="北京今天晴天"),
        ]

    def test_build_context_with_empty_history(self):
        """测试空历史能够正常构建上下文"""
        session = self.create_session()
        question = "你好"

        context = ContextManager.build_context(session, question)

        assert len(context.messages) == 1
        assert isinstance(context.messages[0], HumanMessage)
        assert context.messages[0].content == question

        # 原始历史仍为空
        assert session.history == []

    def test_build_context_with_one_complete_turn(self):
        """测试单个完整轮次能够全部保留"""
        history = self.create_complete_tool_turn()
        session = self.create_session(history)
        question = "今天适合出门吗？"

        context = ContextManager.build_context(session, question)

        # 原始轮次消息全部保留
        assert len(context.messages) == len(history) + 1

        for actual, expected in zip(context.messages[:-1], history):
            assert actual is expected

        # 当前问题位于最后
        assert isinstance(context.messages[-1], HumanMessage)
        assert context.messages[-1].content == question

    def test_build_context_with_multiple_complete_turns(self):
        """测试多个完整轮次按照原始顺序保留"""
        history = [
            HumanMessage(content="问题1"),
            AIMessage(content="回答1"),
            HumanMessage(content="问题2"),
            AIMessage(content="回答2"),
        ]

        session = self.create_session(history)
        question = "问题3"

        context = ContextManager.build_context(session, question)

        expected_contents = [
            "问题1",
            "回答1",
            "问题2",
            "回答2",
            "问题3",
        ]

        actual_contents = [
            message.content
            for message in context.messages
        ]

        assert actual_contents == expected_contents
        assert len(context.messages) == 5

    def test_build_context_keeps_incomplete_last_turn(self):
        """测试末尾不完整轮次不会被丢弃"""
        history = [
            HumanMessage(content="问题1"),
            AIMessage(content="回答1"),
            HumanMessage(content="查询天气"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_weather",
                        "args": {"city": "北京"},
                        "id": "call_002",
                        "type": "tool_call",
                    }
                ],
            ),
        ]

        session = self.create_session(history)
        question = "继续查询"

        context = ContextManager.build_context(session, question)

        # 历史消息全部保留
        assert len(context.messages) == len(history) + 1

        for actual, expected in zip(context.messages[:-1], history):
            assert actual is expected

        # 末尾不完整轮次中的工具调用仍然保留
        assert isinstance(context.messages[-2], AIMessage)
        assert context.messages[-2].tool_calls[0]["id"] == "call_002"

        # 当前问题位于最后
        assert isinstance(context.messages[-1], HumanMessage)
        assert context.messages[-1].content == question

    def test_build_context_does_not_modify_session_history(self):
        """测试构建上下文不会修改原始历史"""
        history = self.create_complete_tool_turn()
        session = self.create_session(history)

        # 保存原始历史快照
        original_history = session.history.copy()
        original_history_id = id(session.history)
        original_message_ids = [
            id(message) for message in session.history
        ]

        ContextManager.build_context(session, "新问题")

        # 历史列表对象没有被替换
        assert id(session.history) == original_history_id

        # 历史消息内容及顺序没有改变
        assert session.history == original_history

        # 历史消息对象没有被替换
        assert [
            id(message) for message in session.history
        ] == original_message_ids
