import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Sequence

from agent.init import AgentRuntimeConfig, Agent
from agent.model import ModelConnectionConfig, ModelConfig
from exception import AgentException


@dataclass(frozen=True)
class AgentCacheKey:
    """agent缓存键"""
    model_name: str
    model_provider: str
    api_key_fingerprint: str
    base_url: str
    temperature: float
    timeout: int
    max_retries: int
    system_prompt_fingerprint: str
    tools_fingerprint: str

class ModelAndAgent:
    agent: Any
    model: Any

class AgentFactory:
    """Agent工厂
    根据本轮运行配置获取或创建agent，并组装 AgentRuntimeConfig
    """
    def __init__(self, max_cache_size: int=32):
        if max_cache_size <= 0:
            raise AgentException("max_cache_size必须大于0")
        self.max_cache_size = max_cache_size
        self._cache: OrderedDict[AgentCacheKey, ModelAndAgent] = OrderedDict() # LRU
        self._lock = RLock()

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @classmethod
    def _get_api_key_fingerprint(cls, connection_config: ModelConnectionConfig) -> str:
        api_key = connection_config.api_key.get_secret_value()
        return cls._sha256(api_key)

    @classmethod
    def _get_tools_fingerprint(
            cls,
            agent_tools: Sequence[Any],
    ) -> str:
        """
        根据 LangChain Tool 的声明计算稳定指纹。
        包含：
            - 工具名称
            - 工具描述
            - 参数 Schema
            - 工具版本
        """
        identities = []
        seen_names = set()
        for tool in agent_tools:
            name = tool.name
            if not name:
                raise AgentException("LangChain Tool 必须具有 name")
            if name in seen_names:
                raise AgentException(f"存在重复工具名称: {name}")
            seen_names.add(name)
            args_schema = tool.args_schema
            if args_schema is None:
                schema = {}
            elif hasattr(args_schema, "model_json_schema"):
                schema = args_schema.model_json_schema()
            else:
                raise AgentException(f"工具 {name} 的 args_schema 不是支持的 Pydantic Schema")

            identities.append({
                "name": name,
                "description": tool.description or "",
                "schema": schema,
                "version": "1",
            })
        # 保留工具列表顺序，避免不同顺序的工具集合被视为相同配置
        serialized = json.dumps(identities,ensure_ascii=False,sort_keys=True,separators=(",", ":"),)
        return cls._sha256(serialized)

    @classmethod
    def _build_cache_key(
            cls,
            model_config: ModelConfig,
            connection_config: ModelConnectionConfig,
            system_prompt: str,
            agent_tools: Sequence[Any],
    ) -> AgentCacheKey:
        return AgentCacheKey(
            model_name=model_config.model_name,
            model_provider=connection_config.model_provider,
            api_key_fingerprint=cls._get_api_key_fingerprint(connection_config),
            base_url=connection_config.base_url,
            temperature=connection_config.temperature,
            timeout=connection_config.timeout,
            max_retries=connection_config.max_retries,
            system_prompt_fingerprint=cls._sha256(system_prompt),
            tools_fingerprint=cls._get_tools_fingerprint(agent_tools),
        )

    def get_agent_runtime_config(
            self,
            model_config: ModelConfig,
            connection_config: ModelConnectionConfig,
            system_prompt: str,
            agent_tools: Sequence[Any]
    ) -> AgentRuntimeConfig:
        """获取本来agent运行配置，相同配置服用Agent，不同配置创建独立的Agent"""
        # 统一确定最终Prompt和Tools，保证缓存键与实际创建Agent使用的配置一致
        cache_key = self._build_cache_key(
            model_config=model_config,
            connection_config=connection_config,
            system_prompt=system_prompt,
            agent_tools=agent_tools
        )
        with self._lock:
            model_agent = self._cache.get(cache_key)
            if model_agent is not None:
                # 移动到末尾，表示最近使用
                self._cache.move_to_end(cache_key)
            else:
                model_agent = ModelAndAgent()
                # 在锁内创建，避免并发请求重复创建相同Agent
                model = Agent.init_llm(model_config=model_config, connection_config=connection_config)
                model_agent.model = model
                agent = Agent.create_agent(model=model, system_prompt=system_prompt, agent_tools=agent_tools)
                model_agent.agent = agent
                self._cache[cache_key] = model_agent
                if len(self._cache) > self.max_cache_size:
                    self._cache.popitem(last=False)
        return AgentRuntimeConfig(
            agent=model_agent.agent,
            model_config=model_config,
            model=model_agent.model,
            connection_config=connection_config,
            system_prompt=system_prompt,
            tools=agent_tools
        )

    def clear_cache(self) -> None:
        """清空Agent缓存"""
        with self._lock:
            self._cache.clear()

    @property
    def cache_size(self) -> int:
        """当前缓存数量"""
        with self._lock:
            return len(self._cache)
