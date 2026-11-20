import json
import math
from typing import Sequence

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage, ToolMessage

from agent.context.token_count.token_count_result import TokenCountCompleteness, TokenCountAccuracy
from agent.context.token_count import TokenCounter
from agent.history import ConversationTurn
from agent.init import SummaryRuntimeConfig
from agent.profile import ProfileFactory
from config import settings
from config.settings import Setting
from exception import AgentException


class SummaryManager:

    def __init__(self):
        """初始化摘要管理器"""
        self.sys_prompt = settings.summary_sys_prompt
        self.runtime_config = self._init_runtime_config(settings)
        self.token_counter=TokenCounter()
        self.budget_config = settings.get_context_budget_config()

    @staticmethod
    def _init_runtime_config(setting: Setting) -> SummaryRuntimeConfig:
        """初始化独立摘要模型"""
        # 获取摘要模型配置
        profile_factory = ProfileFactory(setting)
        model_config, connection_config = profile_factory.get_model_configs(settings.summary_model)
        # 创建独立摘要模型
        model: BaseChatModel = init_chat_model(
            model=model_config.model_name,
            model_provider=connection_config.model_provider,
            api_key=connection_config.api_key.get_secret_value(),
            base_url=connection_config.base_url,
            temperature=connection_config.temperature,
            timeout=connection_config.timeout,
            max_retries=connection_config.max_retries
        )
        return SummaryRuntimeConfig(model=model, model_config=model_config, connection_config=connection_config)


    async def generate_summary(self, turns: Sequence[ConversationTurn]) -> str:
        """
        根据原始历史轮次重新生成完整摘要
        """
        if not turns:
            raise AgentException("摘要历史轮次不能为空")
        history_text=self._serialize_turns(turns)
        if not history_text.strip():
            raise AgentException("摘要历史内容不能为空")
        messages = [
            SystemMessage(content=self.sys_prompt),
            HumanMessage(content=f"请根据以下原始对话生成完整摘要：\n\n{history_text.text}")
        ]
        self._check_input_budget(messages)
        response = await self.runtime_config.model.ainvoke(messages)
        if not isinstance(response.content, str):
            raise AgentException("摘要模型返回了非文本内容")
        summary=response.content.strip()
        if not summary:
            raise AgentException("摘要模型返回内容为空")
        return summary

    def _serialize_turns(self,turns: Sequence[ConversationTurn]) -> str:
        """将完整历史轮次转换为摘要输入文本"""
        contents:list[str]=[]
        for index, turn in enumerate(turns, start=1):
            if not turn.is_complete:
                raise AgentException(f"第{index}轮历史尚未完成，不能参与摘要")
            contents.append(f"## 第{index}轮对话")
            for message in turn.messages:
                message_text=self._serialize_message(message)
                if message_text:
                    contents.append(message_text)
        return "\n\n".json(contents)

    def _serialize_message(self, message: BaseMessage) -> str:
        """序列化单条历史消息"""
        if isinstance(message, SystemMessage):
            return ""
        if isinstance(message, HumanMessage):
            return self._serialize_content("用户", message.content)
        if isinstance(message, AIMessage):
            parts = [self._serialize_content("助手", message.content)]
            if message.tool_calls:
                parts.append("助手工具调用：" + json.dumps(message.tool_calls, ensure_ascii=False, default=str))
            if message.invalid_tool_calls:
                parts.append("助手未解析工具调用："+json.dumps(message.invalid_tool_calls, ensure_ascii=False, default=str))
            return "\n".json(part for part in parts if part)
        if isinstance(message, ToolMessage):
            content = self._serialize_content(f"工具结果({message.name or '未知工具'}", message.content)
            return f"{content}\n工具调用ID：{message.tool_call_id}"
        raise AgentException(f"不支持的摘要消息类型：{type(message).__name__}")

    @staticmethod
    def _serialize_content(role:str, content: str|list) -> str:
        """序列化消息文本内容"""
        if not isinstance(content, str):
            raise AgentException(f"{role}包含非文本内容，当前摘要模块赞不支持多模态消息")
        if not content.strip():
            return ""
        return f"{role}:{content}"

    def _calculate_safety_tokens(self, token_result) -> int:
        """计算摘要请求的安全余量"""

        if token_result.accuracy == TokenCountAccuracy.EXACT:
            return self.budget_config.safety_base_tokens

        estimated_tokens = math.ceil(
            token_result.total_tokens * self.budget_config.safety_ratio
        )

        return self.budget_config.safety_base_tokens + estimated_tokens

    def _check_input_budget(
            self,
            messages: list[BaseMessage],
    ) -> None:
        """检查摘要模型输入是否满足上下文预算"""

        model_config = self.runtime_config.model_config
        connection_config = self.runtime_config.connection_config

        token_result = self.token_counter.count(
            messages=messages,
            model_config=model_config,
            connection_config=connection_config,
            tool_definitions=(),
            add_generation_prompt=True,
        )

        if token_result.completeness == TokenCountCompleteness.INCOMPLETE:
            raise AgentException("摘要模型输入Token统计不完整，无法进行预算判断")
        safety_tokens = self._calculate_safety_tokens(token_result)
        required_tokens = (
                token_result.total_tokens
                + model_config.max_output_tokens
                + safety_tokens
        )

        if required_tokens > model_config.context_window:
            raise AgentException(
                "摘要输入超过模型上下文预算："
                f"输入Token={token_result.total_tokens},"
                f"输出预留={model_config.max_output_tokens},"
                f"安全余量={safety_tokens},"
                f"上下文窗口={model_config.context_window}"
            )

    @staticmethod
    def calculate_covered_turn_count(
            complete_turns: Sequence[ConversationTurn],
            excluded_turns: Sequence[ConversationTurn],
            current_covered_count: int
    ) -> int:
        """计算本次摘要新的覆盖轮数"""
        if current_covered_count < 0:
            raise AgentException("当前摘要覆盖轮数不能小于0")
        if current_covered_count > len(complete_turns):
            raise AgentException("当前摘要覆盖轮数超过完整历史轮次")
        if not excluded_turns:
            return current_covered_count
        # 通过对象身份查找，避免dataclass值相等导致匹配错误
        excluded_indexes=[]
        for excluded_turn in excluded_turns:
            index = next((i for i, turn in enumerate(complete_turns)
                          if turn is excluded_turn),None)
            if index is None:
                raise AgentException("被裁剪的历史轮次不属于当前完整历史")
            excluded_indexes.append(index)
        # 不允许重复轮次
        if len(set(excluded_indexes)) != len(excluded_indexes):
            raise AgentException("被裁剪的历史轮次存在重复")
        excluded_indexes.sort()
        # 新裁剪的轮次必须紧接旧摘要覆盖边界
        expected_indexes = list(range(current_covered_count, current_covered_count+len(excluded_indexes)))
        if excluded_indexes != expected_indexes:
            raise AgentException("本次裁剪历史与当前摘要覆盖边界不连续")
        return current_covered_count + len(expected_indexes)