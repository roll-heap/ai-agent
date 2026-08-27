from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult, GenerationChunk, ChatGenerationChunk

from config.logger_core import log


class LoggingCallbackHandler(BaseCallbackHandler):
    # def on_chain_start(
    #     self,
    #     serialized: dict[str, Any],
    #     inputs: dict[str, Any],
    #     *,
    #     run_id: UUID,
    #     parent_run_id: UUID | None = None,
    #     tags: list[str] | None = None,
    #     metadata: dict[str, Any] | None = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print(f"🚀 on_chain_start 开始执行链")

    # def on_chain_end(
    #     self,
    #     outputs: dict[str, Any],
    #     *,
    #     run_id: UUID,
    #     parent_run_id: UUID | None = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print("✅ on_chain_end 链执行完毕")

    # def on_chain_error(
    #     self,
    #     error: BaseException,
    #     *,
    #     run_id: UUID,
    #     parent_run_id: UUID | None = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print("❌ on_chain_error 链执行错误")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        # 安全提取可能的 tags 或 metadata
        tags = kwargs.get('tags', [])
        if tags and not isinstance(tags, (list, tuple)):
            tags = []  # 如果不是列表，置空
        log.info(f"🔧 on_tool_start 调用工具: \n{serialized.get('name', '未知')}, 参数: {input_str}")

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        # 如果 output 是 ToolMessage 对象，取 content 属性
        if hasattr(output, 'content'):
            content = output.content
        else:
            content = str(output)
        log.info(f"✅ on_tool_end 工具返回: \n{content[:100]}...")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        log.info(f"❌ on_tool_error 调用工具执行失败: {error}")

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        log.info("🤔 on_llm_start 模型开始思考...")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        thingking = response.generations
        # if thingking:
        text = thingking[0][0].text
        # print(f"on_llm_end LLM输出:\n{text}")
        log.info("💡 on_llm_end 模型思考完成")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        log.info(f"❌ on_llm_error 模型出现错误")

    def on_llm_new_token(
        self,
        token: str | list[str | dict[str, Any]],
        *,
        chunk: GenerationChunk | ChatGenerationChunk | None = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        print(token, end="", flush=True)

# 然后在调用时传入
callback = LoggingCallbackHandler()