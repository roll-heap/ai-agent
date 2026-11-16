import json

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

import exception
from agent.context import task_type
from agent.context.task_type import TaskClassificationResult, TaskType
from config import settings, log


class TaskClassifier:
    def __init__(self):
        model_config, connection_config, classifier_sys_prompt = settings.get_classifier_config()
        self.model_config = model_config
        self.connection_config = connection_config
        self.classifier_sys_prompt = classifier_sys_prompt
        # 初始化分类模型
        self.llm = init_chat_model(
            model=self.model_config.model_name,
            model_provider=self.connection_config.model_provider,
            api_key=self.connection_config.api_key,
            base_url=self.connection_config.base_url,
            temperature=self.connection_config.temperature,
            timeout=self.connection_config.timeout,
            max_retries=self.connection_config.max_retries
        )

    def classify(self, text: str) -> TaskClassificationResult:
        """对用户输入进行任务分类"""
        if not text or not text.strip():
            return TaskClassificationResult(task_types=(TaskType.GENERAL,))
        try:
            response = self.llm.invoke([SystemMessage(content=self.classifier_sys_prompt),
                        HumanMessage(content=text)])
        except Exception as e:
            log.exception("任务分类模型调用失败", e)
            return self._general_result()

        try:
            result = json.loads(response.content)
            task_types = tuple(TaskType(item) for item in result["task_types"])
            return TaskClassificationResult(task_types=task_types)
        except Exception as e:
            log.exception("任务分类结果解析是不", e)
            return self._general_result()

    @staticmethod
    def _general_result() -> TaskClassificationResult:
        """返回默认任务分类结果"""
        return TaskClassificationResult(task_types=(TaskType.GENERAL,))
