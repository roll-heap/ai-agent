from dataclasses import dataclass
from enum import Enum

from exception import AgentException


class TaskType(Enum):
    """任务类型"""
    GENERAL = "general"
    CODING = "coding"
    RESEARCH = "research"
    WRITING = "writing"
    QUESTION_ANSWERING = "question_answering"

@dataclass(frozen=True)
class TaskClassificationResult:
    """任务分类结果"""
    task_types: tuple[TaskType, ...]
    def __post_init__(self):
        if not isinstance(self.task_types, tuple):
            raise AgentException("task_types必须是tuple")
        if not self.task_types:
            raise AgentException("task_type不能为空")
        if not all(isinstance(item, TaskType) for item in self.task_types):
            raise AgentException("task_types中的元素必须是TaskType")
        if len(set(self.task_types)) != len(self.task_types):
            raise AgentException("task_types 不能包含重复类型")
        if TaskType.GENERAL in self.task_types and len(self.task_types) > 1:
            raise AgentException("GENERAL 不能与其他任务类型同时出现")