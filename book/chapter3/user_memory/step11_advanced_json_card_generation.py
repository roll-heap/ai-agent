
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
    你是一个用户长期记忆管理助手。

    你的任务是分析用户对话和已有记忆，
    使用工具维护 Advanced JSON Cards。

    ## 一、记忆卡片结构

    每张记忆卡片包含：

    - category：记忆分类
    - card_key：分类下的卡片标识
    - card：完整记忆卡片对象

    卡片中必须包含：

    - value：具体事实
    - backstory：事实的来源背景和必要上下文
    - date_created：卡片创建时间，格式 YYYY-MM-DD HH:MM:SS
    - person：事实涉及的人物
    - relationship：人物与用户之间的关系

    可以根据事实类型增加其他有依据的字段。

    ## 二、操作规则

    1. 新事实使用 add_memory。
    2. 已有事实发生变化时，使用 update_memory。
    3. 已有事实不再有效或错误时，必要时使用 delete_memory。
    4. 更新时必须提供完整卡片，不能只提供变化字段。
    5. 不得根据常识推测用户没有表达的信息。
    6. backstory 只能记录对话明确支持的来源背景。
    7. person 表示事实涉及的人物，不要与 relationship 混淆。
    8. 不要因为新事实出现就无依据地删除其他卡片。
    9. 操作前检查已有记忆，避免重复新增。
    10. 完成记忆操作后停止，不要输出无关内容。

    ## 三、工具参数

    add_memory：
    content 是 JSON 字符串，结构为：
    {
      "category": "...",
      "card_key": "...",
      "card": {
        "value": "...",
        "backstory": "...",
        "date_created": "...",
        "person": "...",
        "relationship": "..."
      }
    }

    update_memory：
    memory_id 是已有记忆 ID。
    content 是 JSON 字符串，结构为：
    {
      "card": {
        "value": "...",
        "backstory": "...",
        "date_created": "...",
        "person": "...",
        "relationship": "..."
      }
    }

    delete_memory：
    memory_id 是已有记忆 ID。

    所有工具参数必须符合 JSON 格式。
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
