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
    你是一个用户记忆卡片生成助手。你的任务是根据用户提供的记忆内容，提取并生成结构化的 Advanced JSON Cards。

    ## 一、任务目标

    将用户提供的记忆内容整理为一个或多个记忆卡片。

    每张卡片应当：
    1. 准确表达用户记忆中的事实。
    2. 保留重要的背景信息和上下文。
    3. 明确记忆涉及的人物及其关系。
    4. 避免重复、臆测或添加用户未提供的信息。
    5. 根据记忆内容选择合适的分类和唯一标识。

    ## 二、输出结构

    必须输出一个 JSON 数组。

    每个数组元素代表一张记忆卡片，包含以下字段：

    - category：记忆分类名称，字符串。
    - card_key：记忆卡片的唯一标识，字符串。
    - card：记忆卡片的具体内容，对象。

    card 必须包含以下字段：

    - value：记忆的核心内容，非空字符串。
    - backstory：记忆的背景信息和上下文，字符串。
    - person：记忆涉及的人物，非空字符串。
    - relationship：记忆涉及的人物关系，非空字符串。

    ## 三、字段生成规则

    ### category
    根据记忆内容选择合适的分类，使用简洁、明确的英文名称。

    ### card_key
    使用简洁、稳定、具有可读性的英文标识。
    同一分类下，不同记忆卡片应使用不同的 card_key。

    ### value
    提取记忆中最重要的事实。
    要求准确、简洁，不得添加原始内容中不存在的信息。

    ### backstory
    补充记忆产生的背景和上下文。
    不要简单重复 value。
    如果没有额外背景信息，使用空字符串。

    ### person
    描述记忆涉及的人物。
    如果涉及多个人物，可以在同一个字符串中描述。
    如果没有明确的人物，使用合理的描述，不得编造人物。

    ### relationship
    描述人物之间与当前记忆相关的关系。
    如果涉及多种关系，可以在同一个字符串中描述。
    如果没有明确的关系，使用合理的描述，不得编造关系。

    ## 四、内容约束

    1. 只能依据用户提供的信息生成记忆。
    2. 不得编造人物、关系、时间、地点或事件。
    3. 不得将推测内容作为确定事实。
    4. 语义相关的内容可以归纳到同一张卡片。
    5. 不同主题的记忆应分别归类。
    6. 避免生成重复的记忆卡片。
    7. 所有字段必须符合指定的数据类型。

    ## 五、严格 JSON 输出约束

    这是最高优先级的输出要求：

    1. 最终响应必须是合法的 JSON 数组。
    2. 第一个非空白字符必须是 [。
    3. 最后一个非空白字符必须是 ]。
    4. 禁止输出 Markdown 代码围栏。
    5. 禁止输出 XML。
    6. 禁止输出自然语言解释。
    7. 禁止输出注释。
    8. 所有字符串必须使用双引号。
    9. 不得在最后一个字段后添加多余逗号。
    10. 不得在 JSON 前后添加任何其他内容。
    11. 输出必须能够被 Python json.loads() 直接解析。

    ## 六、输出示例

    [
      {
        "category": "subscription_info",
        "card_key": "netflix_subscription",
        "card": {
          "value": "用户父亲 John 有一个 Netflix 订阅，目前仍然有效。",
          "backstory": "用户曾替父亲 John 支付 Netflix 费用，该订阅现已激活且保持有效状态。",
          "person": "John（用户父亲）",
          "relationship": "用户是 John 的付费代理人"
        }
      }
    ]

    现在请根据用户提供的记忆内容生成 Advanced JSON Cards。
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
    required_fields = {"category", "card_key", "card"}
    required_card_fields = {"value", "backstory", "person", "relationship"}

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
    response = model.invoke([
        SystemMessage(content=ADVANCED_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                "请根据下面的历史对话提取 Advanced JSON Cards。\n\n"
                "<conversation>\n"
                f"{conversation}\n"
                "</conversation>"
            )
        )]
    )
    # 保留原始模型输出，便于检查提取质量。
    generated_content = extract_text(response.content)
    if not generated_content:
        raise ValueError("模型返回的记忆内容为空")
    # 解析模型返回的 JSON。
    try:
        # cards = json.loads(generated_content)

        # 清理模型可能输出的 Markdown JSON 代码围栏
        generated_content = generated_content.strip()

        if generated_content.startswith("```"):
            generated_content = generated_content.split("\n", 1)[1]
            generated_content = generated_content.rsplit("```", 1)[0].strip()

        cards = json.loads(generated_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型返回的内容不是合法 JSON：{generated_content}") from exc
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
    print(json.dumps(cards,ensure_ascii=False,indent=2))

    print("\n========== 实验结果 ==========")
    print(f"生成卡片数量：{len(cards)}")
    print("Advanced JSON Cards 结构校验通过。")

    # 当前步骤不执行持久化。
    print("当前实验仅完成生成和结构校验，未写入记忆文件。")


if __name__ == "__main__":
    main()
