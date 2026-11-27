
"""
实验 3-2：使用 LLM 自动生成 JSON Cards

实验目标：
1. 将历史对话交给 LLM 分析。
2. 提取值得长期保存的用户事实。
3. 要求 LLM 按 JSON Cards 结构输出。
4. 解析模型返回的 JSON。
5. 保存到 JsonCardsMemoryManager。
6. 输出生成结果和持久化后的记忆上下文。

运行方式（项目根目录）：
python -m book.chapter3.user_memory.step8_json_cards_generation
"""

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.init import Agent
from agent.profile import ProfileFactory
from book.chapter3.user_memory.json_card_memory_manager import (
    JsonCardsMemoryManager,
)
from config import settings


# ============================================================
# 一、实验数据
# ============================================================

# 使用书中用户表达偏好的示例进行记忆提取。
# 不将预期结果直接写入记忆，记忆内容必须由 LLM 从对话中提取。
SAMPLE_CONVERSATION = [
    {
        "role": "user",
        "content": "以后回答涉及数值的内容时，请记得附带单位。",
    },
    {
        "role": "assistant",
        "content": "好的，我会注意在涉及数值时附带相应的单位。",
    },
]

# 使用独立文件，避免影响之前的 JSON Cards 基础实验数据。
STORAGE_PATH = Path(__file__).resolve().parent / "data" / "json_cards_llm_test.json"

SESSION_ID = "session-json-cards-llm-001"


# ============================================================
# 二、JSON Cards 提取 Prompt
# ============================================================

SYSTEM_PROMPT = """
你是一个用户长期记忆提取助手。

你的任务是分析历史对话，提取未来交互中可能有用的用户事实，
并将每条事实组织为 JSON Card。

请遵守以下规则：

1. 只提取用户明确表达或能够可靠确认的信息。
2. 不允许根据常识推测用户没有表达的信息。
3. 不允许将助手提出的问题或未经用户确认的内容当作用户事实。
4. 保留事实的主体、含义和必要上下文。
5. 不要将无关主题强行合并。
6. 优先提取未来交互中有价值的信息。
7. 如果没有值得长期保存的信息，不生成记忆卡片。

每张记忆卡片必须包含以下字段：

{
    "category": "记忆类别",
    "subcategory": "记忆子类别",
    "key": "记忆键",
    "value": "记忆内容"
}

字段说明：
- category：记忆的一级分类。
- subcategory：记忆的二级分类。
- key：当前分类下具有明确含义的记忆键。
- value：具体的用户事实。

输出要求：

1. 只输出合法 JSON，不要输出 Markdown 代码块。
2. 多条记忆使用 JSON 数组表示。
3. 单条记忆使用 JSON 对象表示。
4. 没有值得保存的记忆时，只输出空数组 []。
5. 不要输出解释、分析过程或其他文字。
"""


# ============================================================
# 三、模型初始化
# ============================================================

def init_chat_model():
    """
    复用项目现有模型配置和初始化逻辑。
    """
    # 使用项目当前配置的 qwen3.5:4b 模型。
    model_key = settings.agent_model_map.get("qwen3.5:4b")
    if not model_key:
        raise ValueError("项目中未找到 qwen3.5:4b 对应的模型配置")
    profile_factory = ProfileFactory(settings)
    model_config, connection_config = (
        profile_factory.get_model_configs(model_key)
    )
    # 复用 Agent 已有的模型初始化逻辑。
    model = Agent.init_model(
        model_config=model_config,
        connection_config=connection_config,
    )
    print(f"当前实验模型：{model_config.model_name}")
    return model


# ============================================================
# 四、历史对话格式化
# ============================================================

def format_conversation(messages: list[dict[str, str]]) -> str:
    """
    将结构化消息转换为模型能够理解的对话文本。
    """
    role_mapping = {
        "user": "用户",
        "assistant": "助手",
    }
    conversation_lines = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        # 只处理已知角色。
        if role not in role_mapping:
            continue
        if not isinstance(content, str):
            raise ValueError("对话消息内容必须是字符串")
        conversation_lines.append(
            f"{role_mapping[role]}: {content}"
        )
    conversation = "\n".join(conversation_lines)
    if not conversation.strip():
        raise ValueError("历史对话不能为空")
    return conversation


# ============================================================
# 五、模型输出处理
# ============================================================
def extract_text(content: Any) -> str:
    """
    兼容 LangChain 返回的字符串和内容块列表。
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                text_value = block.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)
        return "\n".join(text_parts).strip()
    raise ValueError("模型返回了不支持的内容类型")


# ============================================================
# 六、JSON Cards 生成
# ============================================================
def generate_json_cards(model: Any,messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    """
    调用 LLM，从历史对话中生成 JSON Cards。
    返回：
        list[dict]：提取到的记忆卡片。
        空列表：没有值得保存的记忆。
    """
    conversation = format_conversation(messages)
    response = model.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "请根据下面的历史对话提取用户长期记忆。\n\n"
                    "<conversation>\n"
                    f"{conversation}\n"
                    "</conversation>"
                )
            ),
        ]
    )
    generated_content = extract_text(response.content)
    if not generated_content:
        raise ValueError("模型返回的记忆内容为空")
    # 解析模型返回的 JSON。
    try:
        cards = json.loads(generated_content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"模型返回的内容不是合法 JSON：{generated_content}"
        ) from exc
    # 统一转换为列表，方便后续逐条保存。
    if isinstance(cards, dict):
        cards = [cards]
    if not isinstance(cards, list):
        raise ValueError("模型返回结果必须是 JSON 对象或数组")
    # 校验每张卡片的数据结构。
    required_fields = {
        "category",
        "subcategory",
        "key",
        "value",
    }
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            raise ValueError(
                f"第 {index + 1} 张记忆卡片必须是 JSON 对象"
            )
        missing_fields = required_fields - card.keys()
        if missing_fields:
            raise ValueError(
                f"第 {index + 1} 张记忆卡片缺少字段："
                f"{sorted(missing_fields)}"
            )
        # 管理器要求分类、子分类、键和 session_id 为非空字符串。
        for field in ("category", "subcategory", "key"):
            value = card[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"第 {index + 1} 张记忆卡片的 "
                    f"{field} 必须是非空字符串"
                )
        # value 可以是字符串或其他 JSON 可序列化值，
        # 但不能缺失或为 null。
        if card["value"] is None:
            raise ValueError(
                f"第 {index + 1} 张记忆卡片的 value 不能为空"
            )
    return cards


# ============================================================
# 七、保存 JSON Cards
# ============================================================
def save_json_cards(manager: JsonCardsMemoryManager,cards: list[dict[str, Any]]) -> list[str]:
    """
    将模型生成的记忆卡片保存到 JSON Cards 管理器。
    返回所有成功新增的记忆 ID。
    """
    memory_ids = []
    for card in cards:
        memory_id = manager.add_memory(
            content=card,
            session_id=SESSION_ID,
        )
        memory_ids.append(memory_id)
    return memory_ids


# ============================================================
# 八、实验入口
# ============================================================
def main() -> None:
    """
    执行一次 JSON Cards 模型生成实验。
    """
    # 1. 初始化模型。
    model = init_chat_model()
    # 2. 初始化 JSON Cards 管理器。
    #    构造函数会自动加载已有持久化数据。
    manager = JsonCardsMemoryManager(STORAGE_PATH)
    # 3. 调用模型生成 JSON Cards。
    cards = generate_json_cards(model=model,messages=SAMPLE_CONVERSATION)
    # 4. 没有提取到记忆时，不执行保存。
    if not cards:
        print("没有提取到值得长期保存的信息。")
        return
    # 5. 保存模型生成的记忆。
    memory_ids = save_json_cards(manager=manager,cards=cards)
    # 6. 输出模型生成结果。
    print("\n========== JSON Cards 模型生成结果 ==========")
    print("生成的记忆卡片：")
    print(json.dumps(cards,ensure_ascii=False,indent=2))
    print("\n保存的记忆 ID：")
    for memory_id in memory_ids:
        print(memory_id)
    # 7. 输出当前记忆上下文。
    print("\n========== JSON Cards 持久化内容 ==========")
    print(manager.get_context_string())
    print(f"\n持久化文件：{STORAGE_PATH}")


if __name__ == "__main__":
    main()
