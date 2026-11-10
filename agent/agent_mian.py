import time

from agent.agent_executor import AgentExecutor
from agent.sesion import Session
from agent.init import Agent
from config import log


if __name__=="__main__":
    # 引入
    agent = Agent.create_agent()
    # 一个会话的历史消息
    session = Session()
    executor = AgentExecutor(agent)
    while True:
        try:
            question = input("请输入问题，如退出，输入【y/退出/exit】\n").strip()
            if not question:
                log.info("请输入问题")
                continue
            if question.lower() in ["y", "退出", "exit"]:
                break
            begin = time.perf_counter()
            executor.execute(session, question)
            elapsed = time.perf_counter() - begin
            log.info(f"执行时间:{elapsed:.2f} s")
            print()
        except KeyboardInterrupt:
            print("\n收到程序关闭，开始退出。")
            break
        except Exception as e:
            log.info(f"执行失败,失败信息：{e}")
    log.info("退出成功".center(60, "="))
