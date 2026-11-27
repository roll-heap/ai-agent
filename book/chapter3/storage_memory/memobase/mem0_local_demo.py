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


USER_ID = "java_architect_demo"
AGENT_ID="mem0_local_demo"
# Mem0本地配置：Ollama + chroma
mem0_config={
    "llm":{
        "provider":"ollama",
        "config":{
            "model":"qwen2.5:3b",
            "temperature":0.1,
            "max_tokens":2000,
            "ollama_base_url":"http://localhost:11434"
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
    original_generate_response = memory.llm.generate_response

    def debug_generate_response(*args, **kwargs):
        print("\n========== Mem0 LLM 请求 ==========")

        print("Response Format:")
        print(kwargs.get("response_format"))

        print("\nUser Prompt:")
        for message in kwargs.get("messages", []):
            if message["role"] == "user":
                print(message["content"])

        result = original_generate_response(*args, **kwargs)

        print("\n========== Mem0 LLM 原始响应 ==========")
        print(repr(result))

        return result

    memory.llm.generate_response = debug_generate_response

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

if __name__=="__main__":
    main()