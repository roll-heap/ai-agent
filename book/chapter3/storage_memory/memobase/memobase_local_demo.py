import time
import uuid
import httpx
from memobase import MemoBaseClient, ChatBlob

# 连接本地 Memobase 服务
client = MemoBaseClient(
    project_url="http://localhost:8019",
    api_key="qazwsxedcrfvtgbyhnujmikolp"
)

client._client.timeout = httpx.Timeout(300.0)
print("当前 HTTP 超时配置：", client._client.timeout)

# 1、检查服务连接
if not client.ping():
    raise RuntimeError("memobase 服务连接失败")
print("memobase 服务连接成功")

# 2、创建或获取用户
# 根据固定名称生成 UUID v5，保证每次运行结果一致
user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "demo_user_wangming"))
user = client.get_or_create_user(user_id)
print(user_id)
# 3、构造对话数据
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
# 4、写入对话记忆
start = time.time()
user.insert(ChatBlob(messages=conversation))
print(f"insert 耗时：{time.time() - start:.2f} 秒")
# 5、同步处理记忆
start = time.time()
user.flush(sync=True)
print(f"flush 耗时：{time.time() - start:.2f} 秒")
print("对话记忆写入完成")
# 6、查询用户画像
print("\n===============查询用户画像================")
print(user.profile())
# 7、查询时间记忆
print("\n===============查询时间记忆================")
print(user.event())
# 8、查询上下文
print("\n===============查询上下文================")
print(user.context())

# from memobase import MemoBaseClient
#
# client = MemoBaseClient(
#     project_url="http://localhost:8019",
#     api_key="qazwsxedcrfvtgbyhnujmikolp",
# )
#
# print("MemoBaseClient 属性：")
# print(vars(client))
#
# print("\nProjectClient 类型：")
# print(type(client.project_client))
#
# print("\nProjectClient 属性：")
# print(vars(client.project_client))
#
# print("\nHTTP Client：")
# http_client = client.project_client.client
# print(type(http_client))
# print("Timeout:", getattr(http_client, "timeout", None))

import httpx
# from memobase import MemoBaseClient
#
# client = MemoBaseClient(
#     project_url="http://localhost:8019",
#     api_key="secret"
# )
#
# http_client = client._client
#
# print("HTTP Client 类型：", type(http_client))
# print("HTTP Client 模块：", type(http_client).__module__)
#
# timeout = http_client.timeout
# print("Timeout 类型：", type(timeout))
# print("Connect timeout：", timeout.connect)
# print("Read timeout：", timeout.read)
# print("Write timeout：", timeout.write)
# print("Pool timeout：", timeout.pool)

#
# import httpx
# from memobase import MemoBaseClient
#
# client = MemoBaseClient(
#     project_url="http://localhost:8019",
#     api_key="secret"
# )
#
# http_client = client._client
#
# print("timeout 属性定义：", getattr(type(http_client), "timeout", None))
# print("timeout 属性 setter：",
#       getattr(getattr(type(http_client), "timeout", None), "fset", None))
#
# print("HTTP Client 内部超时字段：",
#       http_client.__dict__.get("_timeout"))
#
# print("HTTP Client 内部属性：", list(http_client.__dict__.keys()))