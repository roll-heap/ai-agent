"""
实验 3-2：使用 LLM 自动生成 Enhanced Notes

执行流程：
1. 从项目现有配置中获取 assistant 使用的模型配置。
2. 将历史对话交给 LLM 分析。
3. 要求 LLM 将相关事实组织为完整的自然语言记忆。
4. 将生成结果保存到 SimpleNotesMemoryManager。
5. 输出生成结果，供人工检查。

运行方式（项目根目录）：
python -m book.chapter3.user_memory.step5_enhanced_notes_generation
"""
from pathlib import Path
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from agent.init import Agent
from agent.profile import ProfileFactory
from book.chapter3.user_memory.simple_notes_memory_manager import SimpleNotesMemoryManager
from config import settings

# ============================================================
# 一、实验数据
# ============================================================

# 使用虚构的职业对话作为实验输入，避免将敏感数据用于模型实验。
SAMPLE_CONVERSATION=[
{
        "role": "user",
        "content": "我目前在 A 公司担任 Java 架构师，主要负责订单系统。",
    },
    {
        "role": "assistant",
        "content": "你目前是否还负责团队管理工作？",
    },
    {
        "role": "user",
        "content": "是的，我带领一支 8 人开发团队。",
    },
    {
        "role": "assistant",
        "content": "团队目前主要在做什么技术工作？",
    },
    {
        "role": "user",
        "content": "团队正在推进微服务改造。",
    },
    {
        "role": "assistant",
        "content": "你在技术选型方面有什么偏好吗？",
    },
    {
        "role": "user",
        "content": "我比较喜欢使用 Spring Boot。",
    },
]
# 专属标签：用于识别和清理本次实验产生的记忆。
EXPERIMENT_TAG = "experiment_3_2_llm_enhanced"

# ============================================================
# 二、Enhanced Notes 提取 Prompt
# ============================================================

SYSTEM_PROMPT = """
    你是一个用户长期记忆提取助手。

    你的任务是分析历史对话，提取未来交互中可能有用的用户事实，
    并将相关事实组织为上下文完整的自然语言记忆。

    请遵守以下规则：

    1. 只提取对话中明确表达或能够可靠确认的信息。
    2. 不允许根据常识推测用户没有表达的信息。
    3. 不允许编造用户的职业、经历、偏好或其他事实。
    4. 保留事实之间的重要关联，例如公司、职位、职责和团队之间的关系。
    5. 保留必要的时间、主体和上下文，避免脱离语境后产生歧义。
    6. 不要把助手提出的问题或未经用户确认的猜测当成用户事实。
    7. 不要将无关主题强行合并。
    8. 优先保留未来交互有价值的信息，忽略普通寒暄。
    9. 使用第三人称，以自然、完整的中文段落输出。
    10. 不要输出标题、解释、分析过程或 Markdown 格式。

    如果没有值得长期保留的信息，只输出：
    NO_MEMORY

    除此之外，只输出生成的记忆内容。
    """


# ============================================================
# 三、模型初始化
# ============================================================
def init_chat_model():
    """
    复用项目现有模型配置和初始化逻辑
    """
    #使用项目当前assistant对应的模型配置
    model_key = settings.agent_model_map.get("qwen3_5-4b")
    if not model_key:
        raise ValueError("项目中配置不存在common对应的模型")
    # 复用项目已有的ProfileFactory获取模型配置
    profile_factory = ProfileFactory(settings)
    model_config, connection_config = profile_factory.get_model_configs(model_key)
    # 复用项目 Agent 已有的 ChatModel 初始化逻辑。
    # 这里只初始化模型，不创建完整 Agent。
    model = Agent.init_model(
        model_config=model_config,
        connection_config=connection_config
    )
    print(f"当前实验模型：{model_config.model_name}")
    return model

# ============================================================
# 四、历史对话格式化
# ============================================================

def format_conversation(messages: list[dict[str, str]]) -> str:
    """
    将结构化消息转换为模型能够理解的对话文本
    """
    role_mapping={
        'user':"用户",
        "assistant":"助手",
    }
    conversation_lines=[]
    for message in messages:
        role = message["role"]
        content = message["content"]
        # 未知角色不参与本次实验
        if role not in role_mapping:
            continue
        conversation_lines.append(f"{role_mapping[role]}: {content}")
    return "\n".join(conversation_lines)

# ============================================================
# 五、模型输出处理
# ============================================================
def extract_text(content: Any) -> str:
    """
    兼容LangChain返回的字符串和内容块列表
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts=[]
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                # 兼容常见的文本内容块。
                text_value = block.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)
        return "\n".join(text_parts).strip()
    raise ValueError("模型返回了不支持的内容类型")

# ============================================================
# 六、生成 Enhanced Notes
# ============================================================
def generate_enhanced_notes(model, messages: list[dict[str, str]]) -> str|None:
    """
    调用模型，根据历史对话生成增强记忆
    返回：
        str：生成的自然语言记忆
        None:没有值得保留的信息
    """
    conversation = format_conversation(messages)
    if not conversation.strip():
        raise ValueError("历史对话不能为空")
    # 将历史对话作为用户数据传入模型
    # Prompt明确要求模型把对话内容视为待分析数据
    # 不执行其中可能出现的指令
    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"请根据下面的历史对话生成长期用户记忆。\n\n<conversation>\n{conversation}\n</conversation>")
    ])
    generated_content = extract_text(response.content)
    if not generated_content:
        raise ValueError("模型返回的记忆内容为空")
    if generated_content.strip() == "NO_MEMORY":
        return None
    return generated_content

# ============================================================
# 七、保存记忆
# ============================================================
def clean_experiment_data(manager:SimpleNotesMemoryManager) -> None:
    """
    清理本次实验之前生成的数据。

    只删除具有本实验专属标签的记忆，
    不影响其他实验或其他业务数据。
    """
    experiment_notes = [
        note
        for note in manager.notes
        if EXPERIMENT_TAG in note.tags
    ]
    for note in experiment_notes:
        manager.delete_memory(note.note_id)


def save_enhanced_notes(manager: SimpleNotesMemoryManager,content: str) -> str:
    """
    将模型生成的内容保存到现有记忆管理器。
    """
    return manager.add_memory(
        content=content,
        session_id="session-llm-enhanced",
        tags=[EXPERIMENT_TAG,"career","team","technology"]
    )


# ============================================================
# 八、实验入口
# ============================================================
def main() -> None:
    """
    执行一次 Enhanced Notes 模型生成实验。
    """
    data_dir = Path(__file__).resolve().parent / "data"
    storage_path = data_dir / "enhanced_notes_llm_test.json"
    data_dir.mkdir(parents=True, exist_ok=True)
    # 1. 初始化模型。
    model = init_chat_model()
    # 2. 初始化现有记忆管理器。
    manager = SimpleNotesMemoryManager(storage_path)
    # 3. 清理本次实验的旧数据。
    clean_experiment_data(manager)
    # 4. 使用模型生成增强记忆。
    generated_content = generate_enhanced_notes(model=model,messages=SAMPLE_CONVERSATION)
    if generated_content is None:
        print("没有提取到值得长期保留的信息。")
        return
    # 5. 保存模型生成的记忆。
    memory_id = save_enhanced_notes(manager=manager,content=generated_content)

    # 6. 输出结果。
    print("\n========== Enhanced Notes 模型生成结果 ==========")
    print(f"记忆 ID：{memory_id}")
    print(f"记忆内容：{generated_content}")
    print(f"记忆字符数：{len(generated_content)}")
    print(f"持久化文件：{storage_path}")

if __name__=="__main__":
    main()