
"""
实验 3-2：使用 LLM 自动生成 Advanced JSON Cards

当前实验范围：
1. 将历史对话交给 LLM 分析。
2. 提取值得长期保存的用户事实。
3. 按 Advanced JSON Cards 结构生成记忆。
4. 解析模型返回的 JSON。
5. 校验记忆卡片结构。
6. 输出原始结果和校验结果。

当前不执行：
- 记忆持久化
- 多轮记忆更新
- 60 个 YAML 用例评估
"""

import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.init import Agent
from agent.profile import ProfileFactory
from config import settings


# ============================================================
# 一、实验数据
# ============================================================

# 设计一个包含人物、关系和来源背景的对话。
# 这些信息都在对话中明确表达，方便观察模型是否正确提取。
SAMPLE_CONVERSATION = [
    {
        "role": "user",
        "content": (
            "我爸爸 John 之前订阅了 Netflix，"
            "当时是我替他支付的费用。"
            "现在 Netflix 订阅仍然有效。"
        ),
    },
    {
        "role": "assistant",
        "content": "明白了，我会记住这项订阅信息。",
    },
]


# ============================================================
# 二、Advanced JSON Cards Prompt
# ============================================================

ADVANCED_SYSTEM_PROMPT = """
你是一个用户长期记忆提取助手。

你的任务是分析历史对话，提取未来交互中可能有用的用户事实，
并将每条事实组织为 Advanced JSON Card。

每条记忆必须使用以下结构：

{
    "category": "记忆类别",
    "card_key": "稳定的记忆键",
    "card": {
        "value": "具体事实",
        "backstory": "事实的来源背景和产生背景",
        "person": "事实涉及的人物",
        "relationship": "人物与用户之间的关系"
    }
}

字段说明：

1. category：
   记忆所属的一级分类。

2. card_key：
   用于稳定标识同一个业务对象的键。

3. value：
   记录当前明确成立的具体事实。

4. backstory：
   记录理解当前事实所需的来源背景。
   只能记录对话明确支持的信息，不允许自行推测。

5. person：
   表示事实涉及的人物，不一定是用户本人。

6. relationship：
   表示该人物与用户之间的关系。
   如果无法确认，使用 "Unknown"。

提取规则：

1. 只提取用户明确表达或能够可靠确认的信息。
2. 不得将助手提出的内容当作用户事实。
3. 不得根据常识补充对话中不存在的信息。
4. 不要将无关主题强行合并。
5. 同一个业务对象应使用稳定的 card_key。
6. value 与 backstory 应明确区分：
   value 表达事实，backstory 表达事实背景。
7. 不确定的人物信息不得编造。

输出要求：

1. 只输出合法 JSON，不要输出 Markdown 代码块。
2. 多条记忆使用 JSON 数组。
3. 单条记忆使用 JSON 对象。
4. 没有值得保存的信息时输出 []。
5. 不要输出解释、分析过程或其他文字。
"""


# ============================================================
# 三、模型初始化
# ============================================================

def init_chat_model() -> Any:
    """
    复用项目现有模型配置和初始化机制。

    agent_model_map:
        profile_name -> model_config_key

    本实验使用 minicpm5-2b 这个 profile。
    实际模型名称以项目本地配置为准。
    """
    model_key = settings.agent_model_map.get("minicpm5-2b")

    if not model_key:
        raise ValueError(
            "项目配置中未找到 minicpm5-2b 对应的模型映射"
        )

    profile_factory = ProfileFactory(settings)

    model_config, connection_config = (
        profile_factory.get_model_configs(model_key)
    )

    model = Agent.init_model(
        model_config=model_config,
        connection_config=connection_config,
    )

    print(f"当前实验模型：{model_config.model_name}")

    return model


# ============================================================
# 四、历史对话格式化
# ============================================================

def format_conversation(
    messages: list[dict[str, str]],
) -> str:
    """
    将结构化历史消息转换为模型可读的文本。
    """
    role_mapping = {
        "user": "用户",
        "assistant": "助手",
    }

    conversation_lines = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        # 忽略当前实验不支持的角色。
        if role not in role_mapping:
            continue

        if not isinstance(content, str):
            raise ValueError("历史对话内容必须是字符串")

        conversation_lines.append(
            f"{role_mapping[role]}: {content}"
        )

    conversation = "\n".join(conversation_lines)

    if not conversation.strip():
        raise ValueError("历史对话不能为空")

    return conversation


# ============================================================
# 五、模型返回内容提取
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
# 六、Advanced JSON Cards 结构校验
# ============================================================

def validate_advanced_cards(
    cards: Any,
) -> list[dict[str, Any]]:
    """
    校验模型生成的 Advanced JSON Cards。

    注意：
    这里只验证数据结构，不验证模型提取的事实是否真实。
    """

    # 单个对象统一转换为列表。
    if isinstance(cards, dict):
        cards = [cards]

    if not isinstance(cards, list):
        raise ValueError("模型返回结果必须是 JSON 对象或数组")

    required_fields = {
        "category",
        "card_key",
        "card",
    }

    required_card_fields = {
        "value",
        "backstory",
        "person",
        "relationship",
    }

    for index, item in enumerate(cards):

        if not isinstance(item, dict):
            raise ValueError(
                f"第 {index + 1} 张记忆必须是 JSON 对象"
            )

        # 校验外层字段。
        missing_fields = required_fields - item.keys()

        if missing_fields:
            raise ValueError(
                f"第 {index + 1} 张记忆缺少字段："
                f"{sorted(missing_fields)}"
            )

        for field in ("category", "card_key"):
            value = item[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"第 {index + 1} 张记忆的 "
                    f"{field} 必须是非空字符串"
                )

        # 校验内部卡片。
        card = item["card"]

        if not isinstance(card, dict):
            raise ValueError(
                f"第 {index + 1} 张记忆的 card 必须是 JSON 对象"
            )

        missing_card_fields = (
            required_card_fields - card.keys()
        )

        if missing_card_fields:
            raise ValueError(
                f"第 {index + 1} 张记忆的 card 缺少字段："
                f"{sorted(missing_card_fields)}"
            )

        # value 必须是非空字符串。
        if (
            not isinstance(card["value"], str)
            or not card["value"].strip()
        ):
            raise ValueError(
                f"第 {index + 1} 张记忆的 value 必须是非空字符串"
            )

        # backstory 允许空字符串，但必须是字符串。
        if not isinstance(card["backstory"], str):
            raise ValueError(
                f"第 {index + 1} 张记忆的 backstory 必须是字符串"
            )

        # person 和 relationship 必须是非空字符串。
        for field in ("person", "relationship"):
            value = card[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"第 {index + 1} 张记忆的 "
                    f"{field} 必须是非空字符串"
                )

        # 确保模型返回内容能够被 JSON 序列化。
        try:
            json.dumps(item, ensure_ascii=False)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"第 {index + 1} 张记忆包含不可 JSON 序列化的数据"
            ) from exc

    return cards


# ============================================================
# 七、LLM 生成 Advanced JSON Cards
# ============================================================

def generate_advanced_cards(
    model: Any,
    messages: list[dict[str, str]],
) -> tuple[str, list[dict[str, Any]]]:
    """
    调用模型生成 Advanced JSON Cards。

    返回：
        generated_content：模型原始文本
        cards：解析并校验后的卡片列表
    """

    conversation = format_conversation(messages)

    response = model.invoke(
        [
            SystemMessage(content=ADVANCED_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "请根据下面的历史对话提取 Advanced JSON Cards。\n\n"
                    "<conversation>\n"
                    f"{conversation}\n"
                    "</conversation>"
                )
            ),
        ]
    )

    # 保留原始模型输出，便于检查提取质量。
    generated_content = extract_text(response.content)

    if not generated_content:
        raise ValueError("模型返回的记忆内容为空")

    # 解析模型返回的 JSON。
    try:
        cards = json.loads(generated_content)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "模型返回的内容不是合法 JSON："
            f"{generated_content}"
        ) from exc

    # 校验结构。
    validated_cards = validate_advanced_cards(cards)

    return generated_content, validated_cards


# ============================================================
# 八、实验入口
# ============================================================

def main() -> None:
    """
    执行一次 Advanced JSON Cards 生成实验。
    """

    # 1. 初始化模型。
    model = init_chat_model()

    # 2. 调用模型生成记忆。
    raw_output, cards = generate_advanced_cards(
        model=model,
        messages=SAMPLE_CONVERSATION,
    )

    # 3. 输出模型原始结果。
    print("\n========== 模型原始输出 ==========")
    print(raw_output)

    # 4. 输出结构校验结果。
    print("\n========== 校验后的 Advanced JSON Cards ==========")
    print(
        json.dumps(
            cards,
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n========== 实验结果 ==========")
    print(f"生成卡片数量：{len(cards)}")
    print("Advanced JSON Cards 结构校验通过。")

    # 当前步骤不执行持久化。
    print("当前实验仅完成生成和结构校验，未写入记忆文件。")


if __name__ == "__main__":
    main()
