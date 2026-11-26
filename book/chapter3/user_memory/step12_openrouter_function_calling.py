"""
实践 3-2：使用 OpenRouter 验证 Function Calling

当前实践范围：
1. 使用 OpenRouter 接入免费模型。
2. 定义 add_memory 工具。
3. 将工具定义发送给模型。
4. 获取模型返回的工具调用。
5. 解析并输出工具参数。

当前不执行：
- Agent ReAct 循环
- 真实记忆新增
- 记忆持久化
"""
import json
from typing import Any

from openai import OpenAI

# ============================================================
# 一、模型配置
# ============================================================
#OpenRouter API Key
OPENROUTER_API_KEY=""
# OpenRouter 免费模型
MODEL_NAME = "baidu/ernie-5.5-flash-preview:free"
BASE_URL = "https://openrouter.ai/api/v1"


# ============================================================
# 二、工具定义
# ============================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_memory",
            "description": "新增一条用户长期记忆",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "记忆内容，使用 JSON 字符串",
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "记忆标签",
                    },
                },
                "required": ["content"],
            },
        },
    }
]

# ============================================================
# 三、模型初始化
# ============================================================
def init_chat_model() -> OpenAI:
    """
    初始化 OpenRouter 客户端。

    OpenRouter 提供 OpenAI 兼容接口，
    因此直接使用 OpenAI Python SDK。
    """
    if not OPENROUTER_API_KEY or "替换为" in OPENROUTER_API_KEY:
        raise ValueError("请在代码中配置真实的 OpenRouter API Key")
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=BASE_URL,
        timeout=60,
        max_retries=2,
        default_headers={
            "X-Title": "AI Agent Learning",
        },
    )
    print(f"当前实验模型：{MODEL_NAME}")
    print(f"模型服务地址：{BASE_URL}")
    return client


# ============================================================
# 四、Function Calling 测试
# ============================================================
def function_calling(client: OpenAI) -> Any:
    """
    请求模型执行 Function Calling。
    注意：
    本方法只获取模型返回的工具调用信息，
    不负责真正执行 add_memory。
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role":"system",
                "content":"你是一个用户记忆管理助手。\n当用户提供需要长期保存信的信息时，必须调用 add_memory 工具。\n工具参数中的content必须是合法的 JSON 字符串，包含 category、card_key 和 card 字段"
            },
            {
                "role":"user",
                "content":"请记住：我爸爸 John 之前订阅了 Netflix，当时是我替他支付费用，现在订阅仍然有效。"
            }
        ],
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )
    if not response.choices:
        raise ValueError("模型没有返回任何响应")
    print(response.choices[0].message)
    return response.choices[0].message

# ============================================================
# 五、模型工具调用结果解析
# ============================================================
def parse_tool_calls(message: Any) -> None:
    """
    解析模型返回的工具调用。

    当前只解析参数，不执行工具。
    """
    print("\n========== 模型响应 ==========")
    print("普通回答：", message.content)
    tool_calls = message.tool_calls
    if not tool_calls:
        print("\n模型没有返回工具调用。")
        return
    print(f"\n模型返回工具调用数量：{len(tool_calls)}")
    for index, tool_call in enumerate(tool_calls, start=1):
        print(f"\n========== 第 {index} 个工具调用 ==========")
        print("Tool Call ID：", tool_call.id)
        print("工具名称：", tool_call.function.name)
        arguments_text = tool_call.function.arguments
        print("\n原始工具参数：")
        print(arguments_text)
        try:
            arguments = json.loads(arguments_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"工具参数不是合法 JSON：{arguments_text}") from exc
        print("\n解析后的工具参数：")
        print(json.dumps(arguments, ensure_ascii=False, indent=2))

# ============================================================
# 六、实验入口
# ============================================================
def main() -> None:
    """
    执行一次 OpenRouter Function Calling 验证。
    """
    # 1、初始化模型客户端
    client = init_chat_model()
    # 2、请求模型生成工具调用
    message = function_calling(client)
    # 3.解析并输出工具调用
    parse_tool_calls(message)
    print("\n========== 实践结果 ==========")
    print("Function Calling 请求已完成。")
    print("当前仅验证工具调用和参数解析，未执行记忆写入。")

if __name__=="__main__":
    main()