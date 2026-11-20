from threading import RLock
from typing import ClassVar, Sequence, Any

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage, ChatMessage
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from transformers import PreTrainedTokenizerBase, AutoTokenizer

from agent.context.domain import HuggingFaceConfig
from agent.context.token_count import TokenCountResult, TokenCountAccuracy
from agent.context.token_count.token_count_result import TokenCountCompleteness
from agent.context.token_count.provider.base_token_count_provider import BaseTokenCountProvider
from agent.model import ModelConfig, ModelConnectionConfig
from common.utils import AgentUtils
from config import log
from exception import AgentException


class TokenizerProvider(BaseTokenCountProvider):
    """
    基于Hugging Face Tokenizer统计Token
    """
    # ClassVar：这是一个“类变量”，属于类本身，不属于实例，不要把它当成实例字段。
    provider_name: ClassVar[str] = "huggingface"
    priority: ClassVar[int] = 0

    def __init__(self):
        # Tokenizer缓存
        self._tokenizers:dict[tuple[str, str|None], PreTrainedTokenizerBase]={}
        # 保证并发加载安全
        self._lock = RLock()

    def supports(
        self,
        model_config:ModelConfig,
        connection_config: ModelConnectionConfig
    ) -> bool:
        """
        判断是否配置了Hugging Face Tokenizer
        """
        hugging_face_config = model_config.hugging_face_config
        return hugging_face_config is not None and bool(hugging_face_config.name_or_path)

    def count(self,
            messages: Sequence[BaseMessage],
            model_config: ModelConfig,
            connection_config: ModelConnectionConfig,
            tool_definitions: Sequence[BaseTool]=(),
            add_generation_prompt: bool=False
    ) -> TokenCountResult:
        """
        统计消息及工具定义的token数量
        """
        hugging_face_config = model_config.hugging_face_config
        if hugging_face_config is None:
            raise AgentException("当前模型没有配置Hugging Face Tokenizer")
        tokenizer = self._get_tokenizer(hugging_face_config)
        # 1、langchain Message切换
        template_messages = self._convert_messages(messages)
        # 3、当前输入存在工具定义时，统计全部工具
        tool_schemas = None
        if tool_definitions:
            tool_schemas = self._convert_tools(tool_definitions)
        token_ids = self._apply_chat_template(
            tokenizer=tokenizer,
            hugging_face_config=hugging_face_config,
            messages=template_messages,
            tools=tool_schemas,
            add_generation_prompt=add_generation_prompt
        )
        # 4、判断统计精度
        accuracy = TokenCountAccuracy.EXACT if hugging_face_config.runtime_compatible else TokenCountAccuracy.ESTIMATED
        return TokenCountResult(
            total_tokens=len(token_ids),
            accuracy=accuracy,
            completeness=TokenCountCompleteness.COMPLETE
        )


    def _get_tokenizer(self, hugging_face_config) -> PreTrainedTokenizerBase:
        """
        获取Tokenizer，缓存并发复用
        """
        cache_key = (hugging_face_config.name_or_path, hugging_face_config.revision)
        tokenizer = self._tokenizers.get(cache_key)
        if tokenizer is not None:
            return tokenizer
        with self._lock:
            # 双重检查
            tokenizer = self._tokenizers.get(cache_key)
            if tokenizer is not None:
                return tokenizer
            try:
                # 获取当前执行命令的目录，会从hugging face官网下载对应的tokenizer并保存在cache_dir目录下
                project_path = AgentUtils.get_project_root(project_name="ai-agent")
                cache_dir = project_path / "cache" / "hugging_face_cache"/hugging_face_config.name_or_path
                cache_dir.mkdir(parents=True, exist_ok=True)
                tokenizer = AutoTokenizer.from_pretrained(
                    pretrained_model_name_or_path=hugging_face_config.name_or_path,
                    revision=hugging_face_config.revision,
                    cache_dir=cache_dir,
                    local_files_only=True #是否使用本地缓存文件
                ) # type: ignore
                self._tokenizers[cache_key] = tokenizer
                log.info(f"从hugging face获取到的tokenizer:{type(tokenizer).__name__}")
                return tokenizer
            except Exception as e:
                raise AgentException(f"通过huggingFace 加载 tokenizer失败：{type(e).__name__}") from e

    @staticmethod
    def _convert_messages(messages: Sequence[BaseMessage]) -> list[dict[str, Any]]:
        """
        将langchain消息转换为Hugging face消息格式
        """
        result: list[dict[str, Any]]=[]
        for message in messages:
            # 一期只支持纯文本
            if not isinstance(message.content, str):
                raise AgentException(f"暂不支持非文本消息内容:{type(message).__name__}")
            content = message.content
            if isinstance(message, SystemMessage):
                result.append({
                    "role": "system",
                    "content": content
                })
            elif isinstance(message, HumanMessage):
                result.append({
                    "role":"user",
                    "content": content
                })
            elif isinstance(message, AIMessage):
                # 无效工具调用不能静默丢弃
                if message.invalid_tool_calls:
                    raise AgentException("AIMessage 存在无效工具调用，无法完整统计 Token")
                item: dict[str, Any]={"role":"assistant","content":content}
                if message.tool_calls:
                    tool_calls=[]
                    for tool_call in message.tool_calls:
                        tool_name=tool_call.get("name")
                        tool_arguments = tool_call.get("args")
                        call_id = tool_call.get("id")
                        if not isinstance(tool_name, str):
                            raise AgentException("AIMessage工具调用缺少有效名称")
                        if not isinstance(tool_arguments, dict):
                            raise AgentException("AIMessage工具调用参数格式错误")
                        if call_id is None:
                            raise AgentException("AIMessage工具调用没有工具id")
                        tool_call:dict[str, Any]={
                            "id":call_id,
                            "type":"function",
                            "function":{
                                "name":tool_name,
                                "arguments":tool_arguments
                            }
                        }
                        tool_calls.append(tool_call)
                    item["tool_calls"]=tool_calls
                result.append(item)
            elif isinstance(message, ToolMessage):
                if not message.tool_call_id:
                    raise AgentException("ToolMessage 缺少工具调用 ID")
                item = {
                    "role":"tool",
                    "content":content,
                    "tool_call_id": message.tool_call_id
                }
                if message.name:
                    item["name"]=message.name
                #artifact不参与模型输入统计
                result.append(item)
            elif isinstance(message, ChatMessage):
                result.append({
                    "role": message.role,
                    "content":content
                })
            else:
                raise AgentException(f"暂不支持LangChain消息类型：{type(message).__name__}")
        return result

    @staticmethod
    def _apply_chat_template(
            tokenizer: PreTrainedTokenizerBase,
            hugging_face_config: HuggingFaceConfig,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]] | None = None,
            add_generation_prompt:bool=False
    ) -> str | list[int] | list[str] | list[list[int]]:
        """
        通过huggingFace chat template获取Token Id
        """
        kwargs:dict[str, Any]={
            "conversation":messages,
            "tokenize":True,
            "return_dict": False,
            "add_generation_prompt": add_generation_prompt
        }
        if hugging_face_config.chat_template is not None:
            kwargs["chat_template"] = hugging_face_config.chat_template
        if tools is not None:
            kwargs["tools"]=tools
        try:
            # * (单星号)：用于解包列表/元组（或者可迭代对象），作为位置参数传入。
            # func(*[1, 2, 3]) 等价于 func(1, 2, 3)。
            # ** (双星号)：用于解包字典，作为关键字参数传入。
            # func(**{"a": 1, "b": 2}) 等价于 func(a=1, b=2)
            token_ids = tokenizer.apply_chat_template(**kwargs)
            if not isinstance(token_ids, list):
                raise AgentException("chat template未返回预期的Token Id列表")
            return token_ids
        except Exception as e:
            raise AgentException(f"chat template渲染失败：{type(e).__name__}") from e


    @staticmethod
    def _convert_tools(tools: Sequence[BaseTool]) -> list[dict[str, Any]]:
        """
        将LangChain BaseTool转换为OpenAI Function schema
        """
        result: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, BaseTool):
                raise AgentException(f"不支持的工具类型：{type(tool).__name__}")
            result.append(convert_to_openai_tool(tool))
        return result

