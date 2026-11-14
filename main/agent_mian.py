
from agent.context import ContextManager
from agent.factory import AgentFactory
from agent.history import HistoryTurnParser
from agent.model import ModelConfig, ModelConnectionConfig
from agent.profile import ProfileFactory
from agent.session import Session
from config import settings
from main.agent_executor import AgentExecutor


def main():
    # 1. 从 Setting 读取配置
    model_config = ModelConfig(
        model_name=settings.model_name,
        context_window=settings.context_window,
        max_output_tokens=settings.max_output_tokens,
    )

    connection_config = ModelConnectionConfig(
        model_provider=settings.model_provider,
        api_key=settings.api_key,
        base_url=settings.base_url,
        temperature=settings.temperature,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
    )

    # 2. 创建 Agent Profile 注册表
    profile_factory = ProfileFactory(
        model_config=model_config,
        connection_config=connection_config,
    )
    profile_registry = profile_factory.create_registry()

    # 3. 初始化执行依赖
    agent_factory = AgentFactory()

    context_manager = ContextManager(
        history_turn_parser=HistoryTurnParser()
    )

    executor = AgentExecutor(
        agent_factory=agent_factory,
        context_manager=context_manager,
    )

    # 4. 创建一个 Session
    session = Session()

    # 5. 设置默认 Agent
    current_profile = profile_registry.get("assistant")

    print("========== AI Agent ==========")
    print(f"当前 Agent：{current_profile.name}")
    print("输入 /agent 查看可用 Agent")
    print("输入 /agent 名称 切换 Agent")
    print("输入 /exit 退出")

    # 6. 命令行交互
    while True:
        try:
            question = input("\n你：").strip()

            if not question:
                continue

            if question == "/exit":
                print("再见！")
                break

            if question == "/agent":
                print("\n可用 Agent：")
                for profile in profile_registry.list_profiles():
                    print(f"- {profile.name}: {profile.description}")

                print(f"当前 Agent：{current_profile.name}")
                continue

            if question.startswith("/agent "):
                agent_name = question.split(maxsplit=1)[1].strip()

                if not profile_registry.exists(agent_name):
                    print(f"Agent 不存在：{agent_name}")
                    continue

                current_profile = profile_registry.get(agent_name)
                print(f"已切换到 Agent：{current_profile.name}")
                continue

            # 7. 使用当前 Agent 执行本轮请求
            executor.execute(session=session, question=question,profile=current_profile)

        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"\n执行失败：{e}")


if __name__ == "__main__":
    main()
