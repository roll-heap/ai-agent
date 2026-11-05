import asyncio
import time
from datetime import datetime
from agent.sesion import ConversationSession
from agent.conversation import ConversationHandler
from agent.init import Agent
from config import log, trace


@trace
def execute_agent(agent, session:ConversationSession, question: str):

    try:
        async def stream_agent():
            print("\n🤖 正在思考...", flush=True)
            handler = ConversationHandler(agent,session)
            final_answer = await handler.run_agent_turn(question,
                lambda text: print(text, end="", flush=True),
            )
            print()
            return final_answer
        return asyncio.run(stream_agent())
    except Exception as e:
        log.exception(f"执行出错：{e}")
        raise


if __name__=="__main__":
    # 引入
    agent = Agent.create_agent()
    # 一个会话的历史消息
    session = ConversationSession()
    while True:
        try:
            question = input("请输入问题，如退出，输入【y/退出/exit】\n")
            if not question:
                log.info("请输入问题")
                continue
            if question.lower() in ["y", "退出", "exit"]:
                break
            begin_timestamp = datetime.now().timestamp()
            execute_agent(agent, session, question)
            end_timestamp = datetime.now().timestamp()
            log.info(f"执行时间:{end_timestamp - begin_timestamp}")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到程序关闭，开始退出。")
            break
        except Exception as e:
            log.info(f"执行失败,失败信息：{e}")
    log.info("退出成功".center(60, "="))
