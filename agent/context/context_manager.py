from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage
from agent.context.context import AgentContext
from agent.context.task_classifier import TaskClassifier
from agent.history import HistoryTurnParser
from agent.init import AgentRuntimeConfig
from agent.model import TokenCounter
from config import log
from exception import AgentException


class ContextManager:
    """
    1、接收本轮输入和运行配置
        接收 history、current_input、model_config、system_prompt、tools。
    2、任务分类
        调用 TaskClassifier.classify(current_input)，得到 TaskClassificationResult。分类失败时记录错误，使用 GENERAL 作为兜底分类结果，后续走默认预算策略。
    3、历史轮次解析
        调用 HistoryTurnParser，将 Session 的原始历史解析为 ConversationTurn 列表。保留不完整轮次，不修改原始历史。
    4、统计固定输入开销
        使用 TokenCounter 分别统计系统提示词、工具定义和当前输入。
    5、估算输出预算
        将当前输入、任务分类结果和 ModelConfig 传给 OutputTokenBudgetEstimator。
    6、计算安全余量和历史预算
        根据 TokenCountResult 的 accuracy 计算安全余量，再计算可用于历史的 Token 预算。
    7、选择近期原始历史
        调用 HistorySelector，按完整 ConversationTurn 选择连续的近期历史，得到 selected_turns 和 excluded_turns。
    8、准备历史摘要
        将被排除的较早历史、已有摘要、任务分类结果和剩余摘要预算交给 SummaryManager，复用、增量更新或重建摘要。
    9、组装和最终预算检查
        将摘要和近期原始历史按顺序组合，重新计数并检查总预算，形成 AgentContext。
    """
    def __init__(
        self,
        history_turn_parser: HistoryTurnParser,
        task_classifier: TaskClassifier,
        token_counter: TokenCounter,
    ):
        self.history_turn_parser = history_turn_parser
        self.task_classifier = task_classifier
        self.token_counter = token_counter

    def build_context(
            self,
            history: Sequence[BaseMessage],
            current_input: BaseMessage,
            runtime_config: AgentRuntimeConfig
    ) -> AgentContext:
        """
        解析历史消息，并组装本轮 Agent 执行上下文9。
        """
        # 当前阶段只接受 HumanMessage，其他消息类型直接报错。
        if not isinstance(current_input, HumanMessage):
            raise AgentException("当前阶段只接受HumanMessage")
        if runtime_config is None:
            raise AgentException("AgentRuntimeConfig不能为空")
        classification = self.task_classifier.classify(current_input.content)
        log.info(f"当前任务分类结果: {[task_type.value for task_type in classification.task_types]}")

        # 获取本轮模型运行配置，后续Token预算会使用这个配置
        model_config = runtime_config.model_config
        system_prompt = runtime_config.system_prompt
        agent_tools = runtime_config.tools
        log.info(f"当前模型: {model_config.model_name},上下文窗口: {model_config.context_window},最大输出: {model_config.max_output_tokens},工具数量: {len(agent_tools)}")

        turns = self.history_turn_parser.parse_turns(history)
        messages = [message for turn in turns for message in turn.messages]
        messages.append(current_input)
        return AgentContext(
            messages=messages,
            task_classification=classification
        )