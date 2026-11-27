"""
技术栈：
mem0ai                 2.2.1
LLM                    qwen2.5:3b
Embedding              qwen3-embedding:4b
Embedding dimensions   2560
Vector Store           Chroma 本地持久化

python -m pip install mem0ai
python -m pip install chromadb
"""
import json

from mem0 import Memory


USER_ID = "java_architect_demo2"
AGENT_ID="mem0_local_demo"
# Mem0本地配置：Ollama + chroma
mem0_config={
    "llm":{
        "provider":"openai",
        "config":{
            "model":"gpt-6-luna",
            "temperature":0.1,
            "max_tokens":2000,
            "openai_base_url":"",
            "api_key":""
        }
    },
    "embedder":{
        "provider":"ollama",
        "config":{
            "model":"qwen3-embedding:4b",
            "embedding_dims":2560,
            "ollama_base_url":"http://localhost:11434"
        }
    },
    "vector_store":{
        "provider":"chroma",
        "config":{
            "collection_name":"mem0_local_demo",
            "path":"./data/mem0_chroma"
        }
    }
}

def main():
    # 1、初始化记忆系统
    memory = Memory.from_config(mem0_config)
    print(memory)
    # 2、添加用户记忆
    messages = [
        {
            "role":"user",
            "content":"我是一名java资深开发工程师，主要使用java开发企业级项目。\n我正在学习AI Agent，希望使用Python实践AI Agent项目。\n我习惯先理解技术原理，再进行代码实践"
        },
    ]

    # infer=False 先跳过LLM提取记忆
    add_result = memory.add(messages, user_id=USER_ID, agent_id=AGENT_ID)

    print("\n记忆添加结果：")
    print(json.dumps(add_result, ensure_ascii=False, indent=2, default=str))

    # 3、根据问题检索记忆
    query = "用户主要使用什么编程语言？正在学习什么技术？"

    search_result = memory.search(query, filters={
        "user_id":USER_ID,
        "agent_id":AGENT_ID
    }, top_k= 5)

    print("\n记忆检索结果：")
    print(json.dumps(search_result, ensure_ascii=False, indent=2, default=str))

def update_delete():
    memory = Memory.from_config(mem0_config)
    # 1. 新增一条专门用于测试的记忆
    messages = [
        {
            "role": "user",
            "content": "这是一条测试记忆：我目前喜欢喝美式咖啡。"
        }
    ]
    add_result = memory.add(messages=messages, user_id=USER_ID, agent_id=AGENT_ID,)

    print("\n========== 1. 记忆添加成功 ==========")
    print(json.dumps(add_result, ensure_ascii=False, indent=2))

    results = add_result.get("results", [])
    if not results:
        raise RuntimeError("测试记忆创建失败，没有返回记忆 ID")
    memory_id = results[0]["id"]
    print("memory_id:", memory_id)

    # 2. 更新记忆内容
    update_result = memory.update(
        memory_id=memory_id,
        text="这是一条测试记忆：我现在喜欢喝拿铁咖啡。"
    )

    print("\n========== 2. UPDATE ==========")
    print(json.dumps(update_result, ensure_ascii=False, indent=2))

    # 3. 读取记忆，验证更新结果
    updated_memory = memory.get(memory_id)

    print("\n========== 3. GET AFTER UPDATE ==========")
    print(json.dumps(updated_memory, ensure_ascii=False, indent=2))

    # 4. 删除指定记忆
    delete_result = memory.delete(memory_id=memory_id)

    print("\n========== 4. DELETE ==========")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))

    # 5. 查询当前用户的记忆，验证目标 ID 已不存在
    remaining = memory.get_all(
        filters={
            "user_id": USER_ID,
            "agent_id": AGENT_ID
        },
        top_k=100
    )

    remaining_ids = {
        item["id"] for item in remaining.get("results", [])
    }

    print("\n========== 5. VERIFY DELETE ==========")
    print("目标记忆是否仍存在：", memory_id in remaining_ids)

    if memory_id in remaining_ids:
        raise AssertionError("删除验证失败，目标记忆仍然存在")

    print("删除验证通过")

if __name__=="__main__":
    # main()
    update_delete()