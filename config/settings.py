from pathlib import Path

from pydantic import Field, BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent.model import ModelConfig, ModelConnectionConfig
from exception import AgentException

# 获取当前文件（settings.py）所在目录的父目录（即项目根目录）
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class ModelSettings(BaseModel):
    """单个模型的完整配置"""
    model_name: str
    model_provider: str
    api_key: SecretStr
    base_url: str

    temperature: float = 0
    timeout: int = 30
    max_retries: int = 2

    context_window: int
    max_output_tokens: int

class AgentSysPrompt(BaseModel):
    """Agent系统提示词和工具"""
    description: str
    system_prompt: str
    tools: list[str]

class Setting(BaseSettings):
    """应用配置，支持从 .env 和环境变量加载"""
    app_name: str = Field(default="agent", alias="APP_NAME")
    app_version: str = Field(default="0.0.0", alias="APP_VERSION")
    debug: str = Field(default="", alias="APP_LOG_DEBUG")
    host:str = Field(default="", alias="APP_HOST")
    port:int = Field(default=0000, alias="APP_PORT")
    reload:bool = Field(default=True, alias="APP_RELOAD")

    # 日志配置
    log_level:str = Field(default="INFO", alias="LOG_LEVEL")
    log_file:str = Field(default="", alias="LOG_FILE_PATH")

    models: dict[str, ModelSettings] = Field(default_factory=dict, validation_alias="MODELS")
    agent_model_map: dict[str, str] = Field(default_factory=dict, validation_alias="AGENT_MODEL_MAP")
    agent_profile: dict[str, AgentSysPrompt] = Field(default_factory=dict, validation_alias="AGENT_PROFILES")


    classifier_model: str = Field(validation_alias="CLASSIFIER_MODEL")
    classifier_sys_prompt: str = Field(validation_alias="CLASSIFIER_SYSTEM_PROMPT")


    # class Config:
    #     """
    #     pydantic框架里面约定的必须存在的
    #     """
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     case_sensitive = False
    #     extra = "ignore"  # 忽略未定义的变量
    # ============================================================
    # 5. 新版配置（替代 class Config）
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),         # 指定 .env 文件
        env_file_encoding="utf-8",      # 文件编码
        case_sensitive=False,           # 环境变量名不区分大小写
        extra="ignore",                 # 忽略未定义的额外字段
        env_prefix="",                  # 无前缀（保持默认）
        validate_default=False,         # 不验证默认值（提升启动速度）
    )

    def get_classifier_config(self) -> tuple[ModelConfig, ModelConnectionConfig, str]:
        model_settings = self.models.get(self.classifier_model)
        if model_settings is None:
            raise AgentException("分类模型初始化失败")

        model_config = ModelConfig(
            model_name=model_settings.model_name,
            context_window=model_settings.context_window,
            max_output_tokens=model_settings.max_output_tokens
        )
        connection_config = ModelConnectionConfig(
            model_provider=model_settings.model_provider,
            api_key = model_settings.api_key,
            base_url = model_settings.base_url,
            temperature=model_settings.temperature,
            timeout = model_settings.timeout,
            max_retries=model_settings.max_retries
        )
        return model_config, connection_config, self.classifier_sys_prompt


# 全局变量，方便统一管理
settings = Setting()