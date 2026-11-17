import json

import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from config import settings, log


class TaskClassifier:
    def __init__(self):
        model_config, connection_config, classifier_sys_prompt = settings.get_classifier_config()
        self.model_config = model_config
        self.connection_config = connection_config
        self.classifier_sys_prompt = classifier_sys_prompt
        self.llm = ChatOllama(
            model=self.model_config.model_name,
            base_url=self.connection_config.base_url,
            temperature=self.connection_config.temperature,
            num_predict=64,
            format="json",
            reasoning=False,
            client_kwargs={"timeout": self.connection_config.timeout},
        )

    def classify(self, text: str) -> TaskClassificationResult:
        """对用户输入进行任务分类"""
        if not text or not text.strip():
            return self._general_result()
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.classifier_sys_prompt),
                HumanMessage(content=text),
            ])
            result = json.loads(response.content)
            task_types = tuple(TaskType(item) for item in result["task_types"])
            return TaskClassificationResult(task_types=task_types)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            log.exception("任务分类失败: %s", error)
            return self._general_result()

    @staticmethod
    def _general_result() -> TaskClassificationResult:
        """返回默认任务分类结果"""
        return TaskClassificationResult(task_types=(TaskType.GENERAL,))
