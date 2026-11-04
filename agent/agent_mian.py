import asyncio
import time
from datetime import datetime

from agent.conversation import run_agent_turn
from agent.init import Agent
from config import log, trace


@trace
def execute_agent(agent, question: str, messages: list):

    try:
        async def stream_agent():
            print("\n🤖 正在思考...", flush=True)
            final_answer = await run_agent_turn(
                agent,
                messages,
                question,
                lambda text: print(text, end="", flush=True),
            )
            print()
            return final_answer
        return asyncio.run(stream_agent())
    except Exception as e:
        log.exception(f"执行出错：{e}")
        raise


if __name__=="__main__":
    log.info("=" * 30)
    log.info("智能助手")
    log.info("=" * 30)
    # 引入
    agent = Agent.create_agent()
    messages = []
    while True:
        question = input("请输入问题，如退出，输入【y/退出/exit】\n")
        if not question:
            log.info("请输入问题")
            continue
        if question.lower() in ["y", "退出", "exit"]:
            break
        begin_timestamp = datetime.now().timestamp()
        execute_agent(agent, question, messages)
        end_timestamp = datetime.now().timestamp()
        log.info(f"执行时间:{end_timestamp - begin_timestamp}")
        time.sleep(1)
    log.info("退出成功".center(60, "="))
