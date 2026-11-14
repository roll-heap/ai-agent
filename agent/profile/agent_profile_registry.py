from typing import Iterable

from agent.profile.agent_profile import AgentProfile
from exception import AgentException


class AgentProfileRegistry:
    """agent注册表配置
    负责AgentProfile的注册，查询和列表展示
    """
    def __init__(self, profiles: Iterable[AgentProfile] | None = None):
        self._profiles: dict[str, AgentProfile] = {}
        if profiles is not None:
            for profile in profiles:
                if profile.name and profile.name not in self._profiles:
                    self._profiles[profile.name] = profile

    def get(self, name: str) -> AgentProfile | None:
        """根据名称获取agent配置"""
        profile = self._profiles.get(name)
        if profile is None:
            raise AgentException("未获取到模型配置")
        return profile

    def list_profiles(self) -> list[AgentProfile]:
        """获取全部Agent配置"""
        return list(self._profiles.values())

    def exists(self, name: str) -> bool:
        """判断Agent是否已注册"""
        return name in self._profiles

    @property
    def names(self) -> tuple[str, ...]:
        """
        获取所有 Agent 名称。
        """
        return tuple(self._profiles.keys())