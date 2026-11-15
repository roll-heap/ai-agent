
from agent.context import ContextManager
from agent.factory import AgentFactory
from agent.history import HistoryTurnParser
from agent.profile import ProfileFactory
from agent.session import Session
from config import settings
from main.agent_executor import AgentExecutor


def main():
    # 1. 创建 Agent Profile 注册表，根据.env读取到settings中，将配置注入到Factory中，包括Model配置，agent的系统配置
    profile_factory = ProfileFactory(settings)
    # 获取注册器，根据注册器可以获取不同模型的配置
    profile_registry = profile_factory.create_registry()
    # 2. 初始化执行依赖 获取Agent
    agent_factory = AgentFactory()
    context_manager = ContextManager(history_turn_parser=HistoryTurnParser())
    executor = AgentExecutor(agent_factory=agent_factory,context_manager=context_manager,)
    # 3. 创建一个 Session
    session = Session()
    # 4. 设置默认 Agent
    current_profile = profile_registry.get("assistant")
    print("========== AI Agent ==========")
    print(f"当前 Agent：{current_profile.name}")
    print("输入 /agent 查看可用 Agent")
    print("输入 /agent 名称 切换 Agent")
    print("输入 /exit 退出")
    # 5. 命令行交互
    while True:
        try:
            question = input("\n你：").strip()
            if not question:
                continue
            if question == "/exit":
                print("再见！")
                break
            parts = question.split(maxsplit=1)
            if parts[0] == "/agent":
                if len(parts) == 1:
                    print("\n可用 Agent：")
                    for profile in profile_registry.list_profiles():
                        print(f"- {profile.name}: {profile.description}")
                    print(f"当前 Agent：{current_profile.name}")
                    continue
                agent_name = parts[1].strip()
                if not profile_registry.exists(agent_name):
                    print(f"Agent 不存在：{agent_name}")
                    continue
                current_profile = profile_registry.get(agent_name)
                print(f"已切换到 Agent：{current_profile.name}")
                continue
            # 6. 使用当前 Agent 执行本轮请求
            answer = executor.execute(session=session, question=question, profile=current_profile)
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"\n执行失败：{e}")


if __name__ == "__main__":
    main()
