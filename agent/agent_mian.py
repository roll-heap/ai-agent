import asyncio
import time
from datetime import datetime

from agent.init.init_agent import Agent
from config.logger_core import log, trace


@trace
def execute_agent(agent, question: str, messages: list):

    try:
        messages.append({"role": "user","content": question})
        async def stream_agent():
            final_answer = ""
            print("\n🤖 正在思考...", flush=True)
            async for event in agent.astream_events(
                {"messages": messages},
                version="v2"
            ):
                kind = event["event"]
                # ==========================
                # LLM 输出
                # ==========================
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        content = chunk.content
                        if isinstance(content, str):
                            print(content, end="", flush=True )
                            final_answer += content
                # ==========================
                # Tool 开始
                # ==========================
                elif kind == "on_tool_start":
                    tool_name = event.get("name","未知工具")
                    tool_input = event["data"].get("input",{})
                    print(f"\n🔧 调用工具：{tool_name}" f"\n   参数：{tool_input}")
                # ==========================
                # Tool 结束
                # ==========================
                elif kind == "on_tool_end":
                    output = event["data"].get("output", "" )
                    print(f"\n✅ 工具返回：" f"{str(output)[:200]}")
            # ==========================
            # Agent 整体执行完成
            # ==========================
            print()
            if final_answer:
                messages.append({"role": "assistant","content": final_answer})
            return final_answer
        return asyncio.run(stream_agent())
    except Exception as e:
        log.exception(f"执行出错：{e}")
        # 回滚用户消息
        if (messages
            and messages[-1]["role"] == "user"
        ):
            messages.pop()
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