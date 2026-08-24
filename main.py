import time
from datetime import datetime

from agent.init.agent import Agent
from config.logger_core import log, trace


@trace
def execute_agent(agent, question:str, messages:list):
    try:
        # agent 直接调用 .invoke()，输入格式为消息列表[reference:1]
        # 追加用户消息历史
        log.info(f"\n用户问了：\n{question}，将其加入上下文记忆，开始进行思考")
        messages.append({"role":"user", "content":question})
        # 把完整历史传给 Agent
        result = agent.invoke({"messages":messages})
        ai_response = result["messages"][-1].content
        log.info(f"\nAI回答结果：\n{ai_response}，\n将其添加AI回复历史")
        messages.append({"role":"assistant", "content":ai_response})
    except Exception as e:
        log.exception(f"执行出错：{e}")
        # 异常时回滚用户消息，将其从记忆上下文中移除，保持上下文干净，因为异常后最近的这个消息并没有AI的回复
        if messages and messages[-1]["role"] == "user":
            messages.pop()

if __name__=="__main__":
    # set_trace_id()
    log.info("=" * 60)
    log.info("智能天气助手（LangChain 1.0 + DeepSeek）")
    log.info("=" * 60)
    # 引入
    agent = Agent.create_agent()
    messages = []
    while True:
        question = input("请输入城市名称，查询天气？退出，请输入【y/退出/exit】\n")
        if not question:
            log.info("请输入城市名")
            continue
        if question.lower() in ["y", "退出", "exit"]:
            break
        begin_timestamp = datetime.now().timestamp()
        execute_agent(agent, question, messages)
        end_timestamp = datetime.now().timestamp()
        log.info(f"执行时间:{end_timestamp - begin_timestamp}")
        time.sleep(1)
    log.info("退出成功".center(60, "="))