from collections.abc import Callable, Sequence
from dataclasses import dataclass
from agent.sesion import Session
from config import log
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, HumanMessage
from exception import AgentException

@dataclass
class ConversationTurn:
    """一轮对话及其完整性状态"""
    messages: list[BaseMessage]
    is_complete: bool

class ConversationUtils:
    """
    会话处理工具类，处理agent交互过程中的对话
    """

    @staticmethod
    def handle_tool_events(
        messages: Sequence[BaseMessage],
        tool_names: dict[str, str],
        seen_tool_calls: set[str],
        seen_tool_results: set[str],
        on_text: Callable[[str], None],
    ) -> None:
        """
        识别 AIMessage 中的工具调用。
        记录 tool_call_id 与工具名称的关系。
        识别 ToolMessage 并展示工具结果。
        """
        for message in messages:
            if isinstance(message, AIMessage):
                for tool_call in message.tool_calls:
                    tool_call_id = tool_call.get("id")
                    tool_name = tool_call["name"]

                    if tool_call_id:
                        tool_names[tool_call_id] = tool_name

                    call_key = (
                        tool_call_id
                        or f"{tool_name}:{tool_call['args']!r}"
                    )

                    if call_key not in seen_tool_calls:
                        on_text(f"\n🔧 调用工具：{tool_name} 参数：{tool_call['args']}\n")
                        seen_tool_calls.add(call_key)

            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                result_key = (tool_call_id or f"{message.name}:{message.text}")
                if result_key not in seen_tool_results:
                    tool_name = tool_names.get(tool_call_id, message.name or "unknown_tool",)
                    on_text(f"\n✅ 工具返回（{tool_name}）: {message.text}\n")

                    seen_tool_results.add(result_key)


    @staticmethod
    def get_final_answer(messages: Sequence[BaseMessage]) -> str:
        """提取最后一条非工具调用的 AI 回复。"""
        for message in reversed(messages):
            if isinstance(message, AIMessage) and not message.tool_calls:
                return message.text
        return ""

    @staticmethod
    def message_summary(messages: Sequence[BaseMessage]) -> str:
        """生成用于排障的完整消息协议详情。"""
        summary = []
        for index, message in enumerate(messages):

            if isinstance(message, AIMessage):
                tool_calls = [
                    {
                        "name": call["name"],
                        "id": call["id"],
                        "args": call["args"],
                    }
                    for call in message.tool_calls
                ]

                summary.append(
                    f"{index}:ai("
                    f"content={message.text!r}, "
                    f"tool_calls={tool_calls})"
                )

            elif isinstance(message, ToolMessage):
                summary.append(
                    f"{index}:tool("
                    f"name={message.name}, "
                    f"tool_call_id={message.tool_call_id}, "
                    f"content={message.text!r})"
                )

            else:
                summary.append(
                    f"{index}:{message.type}"
                    f"(content={message.text!r})"
                )

        return " | ".join(summary)

    @staticmethod
    def validate_tool_protocol(messages: Sequence[BaseMessage]) -> None:
        """
        校验本轮工具调用与工具返回是否完整匹配。
            规则	                                说明
        调用 ID 唯一	            同一回合不能重复出现相同的工具调用 ID
        返回必须有对应调用	        ToolMessage 的 tool_call_id 必须能找到对应的 AIMessage 工具调用
        每次调用必须有返回	        每个工具调用 ID 都必须存在对应的 ToolMessage
        通过： AIMessage: call_001 ToolMessage: call_001
        不通过：AIMessage: call_001 ToolMessage: call_002
        不通过：AIMessage: call_001 ToolMessage: （缺失）
        """
        # 检查工具调用是否重复
        tool_call_ids = set()
        # 检查工具返回是否重复。
        tool_result_ids = set()
        for message in messages:
            # 收集AI发起的工具调用
            if isinstance(message, AIMessage):
                # 校验tool_call_id的有效性
                for tool_message in message.tool_calls:
                    tool_call_id = tool_message.get("id")
                    if not tool_call_id:
                        raise AgentException("工具调用缺少有效的tool_call_id")
                    if tool_call_id in tool_call_ids:
                        raise AgentException(f"发现重复的工具调用ID:{tool_call_id}")
                    tool_call_ids.add(tool_call_id)
            # 收集工具返回
            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                if not tool_call_id:
                    raise AgentException("工具返回缺少有效的tool_call_id")
                if tool_call_id in tool_result_ids:
                    raise AgentException(f"发现重复的工具返回ID:{tool_call_id}")
                tool_result_ids.add(tool_call_id)
        # 检查是否存在未返回的工具调用  集合差集
        missing_result = tool_call_ids - tool_result_ids
        # 检查是否存在没有对应调用的工具返回  集合差集
        orphan_results = tool_result_ids - tool_call_ids
        if missing_result or orphan_results:
            raise AgentException(f"工具调用协议不完整 ｜ 缺少返回:{missing_result} | 缺少调用:{orphan_results}")

    @staticmethod
    def split_conversation_turns(messages: Sequence[BaseMessage]) -> list[ConversationTurn]:
        """根据HumanMessages划分对话轮次，并判定每轮是否完整,这里处理消息为了压缩历史会话，所以只针对HumanMessage,AIMessage,ToolMessage
            最终完整性判定：
            一轮对话必须同时满足：
            1. 以 HumanMessage 开始。
            2. 每个工具调用都有唯一的 tool_call_id。
            3. 每个工具调用都有且只有一个对应的 ToolMessage。
            4. 所有工具调用结果返回后，至少出现一条不带 tool_calls 的 AIMessage。
            5. 不存在工具协议异常。
            另外，轮次边界仍然由下一条 HumanMessage 确定。

            1、用户输入  HumanMessage("查一下北京的天气")
            2、第一次请求 LLM   LLM 根据用户问题和工具定义，决定调用 query_weather。 AIMessage(tool_calls=[...])
            3、执行工具  调用 query_weather(city="北京")，得到天气数据。 ToolMessage(tool_call_id="call_001", content="晴天...")
            4、第二次请求 LLM 将工具结果和之前的消息一起发送给 LLM。   LLM 根据工具结果组织最终回答。
            5、最终回答  AIMessage(content="北京今天是晴天……")
            即：HumanMessage -> AIMessage() -> ToolMessage() -> AIMessage
        """
        turns: list[ConversationTurn] = []
        current_messages: list[BaseMessage] = []
        # 当前轮次尚未得到返回的工具调用ID
        pending_tool_call_ids: set[str] = set()
        # 当前轮次已经出现过的工具调用ID
        seen_tool_call_ids: set[str] = set()
        # 是否出现过不带tool_calls的AIMessage
        has_final_ai = False
        # 是否发现工具协议异常
        has_protocol_error = False

        def finish_turn() -> None:
            """结束当前轮次，并记录完整性"""
            # nonlocal 表示：如果在这个嵌套函数中需要重新给外层函数的变量赋值，那么操作的是外层变量，而不是创建一个同名的局部变量
            # nonlocal current_messages
            if not current_messages:
                return
            # has_final_ai	本轮至少出现过一条不带工具调用的 AIMessage
            # not pending_tool_call_ids	所有工具调用都已经收到结果
            # not has_protocol_error	没有缺失 ID、重复调用或异常返回
            is_complete = (has_final_ai and not pending_tool_call_ids and not has_protocol_error)
            turns.append(ConversationTurn(messages=current_messages.copy(),is_complete=is_complete))

        for message in messages:
            # 1 新的HumanMessage表示上一轮结束
            if isinstance(message, HumanMessage):
                finish_turn()
                #开始新一轮，重置状态
                current_messages = [message]
                pending_tool_call_ids = set()
                seen_tool_call_ids = set()

                has_final_ai = False
                has_protocol_error = False
                continue
            if not isinstance(message, (AIMessage, ToolMessage)):
                raise AgentException(f"不支持的消息类型：{type(message).__name__}")
            # 当前没有HumanMessage,却出现了其他消息
            if not current_messages:
                raise AgentException("历史消息必须以HumanMessage开始")
            # 添加AIMessage， ToolMessage
            current_messages.append(message)

            #2 处理AIMessage
            if isinstance(message, AIMessage):
                if message.tool_calls:
                    has_final_ai = False
                    for tool_call in message.tool_calls:
                        tool_call_id = tool_call.get("id")
                        if not tool_call_id:
                            has_protocol_error = True
                            continue
                        if tool_call_id in seen_tool_call_ids:
                            has_protocol_error = True
                            continue
                        seen_tool_call_ids.add(tool_call_id)
                        pending_tool_call_ids.add(tool_call_id)
                else:
                    has_final_ai = True

            #3 处理ToolMessage
            elif isinstance(message, ToolMessage):
                tool_call_id = message.tool_call_id
                # 工具协议不完整，没有tool_call_id 或者 不是本轮的tool_call_id
                if not tool_call_id or tool_call_id not in pending_tool_call_ids:
                    has_protocol_error = True
                else:
                    pending_tool_call_ids.remove(tool_call_id)
                    has_final_ai = False
        # 4 遍历结束，处理最后一轮
        finish_turn()
        return turns