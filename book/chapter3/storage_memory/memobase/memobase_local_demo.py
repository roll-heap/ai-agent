"""
技术栈：memobase 服务   LLM qwen2.5:3b  PostgreSQL:17g
docker运行： memobase 服务，PostgreSQL，redis
说明：
执行到这里的时候 user.flush(sync=True)
memobase会调用LLM进行记忆提取，然后保存记忆，执行redis，PostgreSQL
"""
import time
import uuid
import httpx
from memobase import MemoBaseClient, ChatBlob

def clear_user_memory(user):
    """删除指定用户的全部 Profile 和 Event，保留用户账号。"""

    # 1. 获取并删除 Profile
    profiles = user.profile()

    profile_count = 0
    for profile in profiles:
        profile_id = profile.id
        if user.delete_profile(profile_id):
            profile_count += 1

    # 2. 获取并删除 Event
    events = user.event(topk=1000)

    event_count = 0
    for event in events:
        event_id = event.id
        if user.delete_event(event_id):
            event_count += 1

    print(f"Profile 删除数量：{profile_count}/{len(profiles)}")
    print(f"Event 删除数量：{event_count}/{len(events)}")

    return profile_count, event_count


# 连接本地 Memobase 服务
client = MemoBaseClient(
    project_url="http://localhost:8019",
    api_key="qazwsxedcrfvtgbyhnujmikolp"
)

client._client.timeout = httpx.Timeout(300.0)
print("当前 HTTP 超时配置：", client._client.timeout)

# # 1、检查服务连接
if not client.ping():
    raise RuntimeError("memobase 服务连接失败")
print("memobase 服务连接成功")
#
# # 2、创建或获取用户
# # 根据固定名称生成 UUID v5，保证每次运行结果一致
user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "demo_user_liming"))
user = client.get_or_create_user(user_id)
print(user_id)
# # 3、构造对话数据
conversation = [
    {
        "role":"user",
        "content":"我叫王明，是一名java架构师，目前正在学习AI Agent"
    },
    {
        "role":"assistant",
        "content":"很高兴认识你，我会记住这些信息"
    },
    {
        "role":"user",
        "content": "我主要是用java，也有python基础，希望掌握AI agent开发"
    },
    {
        "role":"assistant",
        "content":"了解，你希望结合已有的java技术经验学习AI agent"
    }
]
# # 4、写入对话记忆
start = time.time()
user.insert(ChatBlob(messages=conversation))
print(f"insert 耗时：{time.time() - start:.2f} 秒")
# # 5、同步处理记忆
start = time.time()
user.flush(sync=True)
print(f"flush 耗时：{time.time() - start:.2f} 秒")
print("对话记忆写入完成")
# # 6、查询用户画像
print("\n===============查询用户画像================")
print(user.profile())
# # 7、查询时间记忆
print("\n===============查询时间记忆================")
print(user.event())
# # 8、查询上下文
print("\n===============查询上下文================")
print(user.context())

# 9、删除记忆
# clear_user_memory(user)