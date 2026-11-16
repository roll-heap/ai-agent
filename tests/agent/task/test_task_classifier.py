from agent.context import TaskClassifier


def test_task_classifier():
    classifier = TaskClassifier()

    result = classifier.classify("帮我分析这段 Python 代码的性能问题")

    print(result)
    print(result.task_types)