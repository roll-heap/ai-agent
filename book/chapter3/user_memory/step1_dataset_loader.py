from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Literal, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

EXPECTED_COUNTS={
    "layer1":20,
    "layer2":20,
    "layer3":20
}

class Message(BaseModel):
    """一条对话消息的数据结构"""
    model_config = ConfigDict(extra="ignore")
    role: str = Field(min_length=1)
    content: str = Field(min_length=1)

class ConversationHistory(BaseModel):
    """一次完整的历史回话"""
    model_config = ConfigDict(extra="ignore")
    conversation_id: str=Field(min_length=1)
    timestamp: str | date | datetime | None = None
    messages:list[Message] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MemoryTestCase(BaseModel):
    """一个记忆能力评估用例"""
    model_config = ConfigDict(extra="ignore")
    test_id: str=Field(min_length=1)
    category:Literal["layer1","layer2","layer3"]
    title:str=Field(min_length=1)
    # 提供记忆形成所需的历史信息，记忆写入和更新
    conversation_histories: list[ConversationHistory]=Field(min_length=1)
    # 检验最终记忆是否能支持回答，记忆检索和回答
    user_question:str=Field(min_length=1)
    # 判断回答是否符合预期，结果评估
    evaluation_criteria:str=Field(min_length=1)
    # 描述理想的 Agent 行为，结果分析
    expected_behavior:str|None=None

def load_test_case(file_path: Path) -> MemoryTestCase:
    """读取单个YAML文件，并转换为结构化对象"""
    # 读取YAML原始内容
    raw_data=yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError(f"测试文件格式错误：{file_path.name}")
    try:
        # 使用 Pydantic 校验字段和数据类型
        return MemoryTestCase.model_validate(raw_data)
    except ValidationError as exc:
        # 不打印原始输入，避免错误日志泄露测试数据内容
        details = "; ".join(
            f"{'.'.join(str(x) for x in item['loc'])}: {item['msg']}"
            for item in exc.errors(include_input=False)
        )
        raise ValueError(f"测试文件数据校验失败：{file_path.name}, {details}") from exc

def load_dataset(dataset_dir: Path) -> list[MemoryTestCase]:
    """加载三个层次的全部测试用例"""
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"数据集目录不存在:{dataset_dir}")
    # 按文件路径排序，保证每次加载顺序一致
    yaml_files = sorted(dataset_dir.glob("layer*/*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"没有找到YAML测试文件：{dataset_dir}")
    cases: list[MemoryTestCase] = []
    for file_path in yaml_files:
        case = load_test_case(file_path)
        # 检查目录层次和文件内部生命的层次是否一致
        if file_path.parent.name != case.category:
            raise ValueError(f"测试层次不一致：{file_path.name}")
        cases.append(case)
    return cases

def validate_dataset(cases: list[MemoryTestCase]) -> None:
    """检查整个数据集是否符合实验要求"""
    #校验测试用例ID是否重复
    test_ids=[case.test_id for case in cases]
    if len(test_ids) != len(set(test_ids)):
        raise ValueError("发现重复的 test_id")
    # 统计三个层次的用例数量
    actual_counts = Counter(case.category for case in cases)
    for layer, expected_count in EXPECTED_COUNTS.items():
        actual_count = actual_counts.get(layer, 0)
        if actual_count != expected_count:
            raise ValueError(f"{layer}数量错误，期望 {expected_count}，实际 {actual_count}")
    if len(cases) != 60:
        raise ValueError(f"测试用例总数错误: 期望60， 实际{len(cases)}")


def print_summary(cases: list[MemoryTestCase]) -> None:
    """输出数据集统计信息，不打印原始对话内容"""
    layer_counts = Counter(case.category for case in cases)
    total_sessions = sum(len(case.conversation_histories) for case in cases)
    total_messages = sum(len(history.messages) for case in cases for history in case.conversation_histories)
    print("========== 实验数据集校验结果 ==========")
    print(f"测试用例总数：{len(cases)}")
    for layer in EXPECTED_COUNTS:
        print(f"{layer}：{layer_counts[layer]}")
    print(f"历史会话总数：{total_sessions}")
    print(f"消息总数：{total_messages}")
    print("数据集校验通过！")

def main(data_path: Path) -> int:
    """程序入口
    python book/chapter3/user_memory/step1_dataset_loader.py -
-dataset-dir book/chapter3/user_memory/test_cases
    """
    # parser = argparse.ArgumentParser(description="实验 3-2：记忆评估数据集加载与校验")
    # parser.add_argument(
    #     "--dataset-dir",
    #     type=Path,
    #     required=True,
    #     help="书籍配套评估数据集目录",
    # )
    # args = parser.parse_args()
    try:
        # cases = load_dataset(args.dataset_dir)
        cases = load_dataset(data_path)
        validate_dataset(cases)
        print_summary(cases)
        return 0
    except (OSError, ValueError) as exc:
        print(f"数据集加载失败：{exc}")
        return 1


if __name__ == "__main__":
    path = Path(__file__).resolve().parent
    print(path / "test_cases")
    main(path / "test_cases")