from dataclasses import dataclass
from typing import Any

from agent.model import ModelConfig, ModelConnectionConfig


@dataclass(frozen=True)
class AgentProfile:
    name: str
    description: str
    model_config: ModelConfig
    connection_config: ModelConnectionConfig
    system_prompt: str
    tools: tuple[Any, ...]