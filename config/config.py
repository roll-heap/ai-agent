from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from exception import ErrorEnum, AgentException

# 获取当前文件（config.py）所在目录的父目录（即项目根目录）
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Setting(BaseSettings):
    """应用配置，支持从 .env 和环境变量加载"""
    app_name: str = Field(default="agent", alias="APP_NAME")
    app_version: str = Field(default="0.0.0", alias="APP_VERSION")
    debug: str = Field(default="", alias="APP_LOG_DEBUG")
    host:str = Field(default="", alias="APP_HOST")
    port:int = Field(default=0000, alias="APP_PORT")
    reload:bool = Field(default=True, alias="APP_RELOAD")

    # 模型配置
    model: str = Field(default="deepseek-chat", alias="MODEL")
    api_key: SecretStr = Field(..., alias="API_KEY")
    base_url:str = Field(default="https://api.deepseek.com", alias="BASE_URL")
    temperature:float = Field(default=0, alias="TEMPERATURE")
    timeout:int = Field(default=30, alias="TIMEOUT")
    max_retries:int = Field(default=2, alias="MAX_RETRIES")

    # 日志配置
    log_level:str = Field(default="INFO", alias="LOG_LEVEL")
    log_file:str = Field(default="", alias="LOG_FILE_PATH")


    @classmethod
    @field_validator("base_url")
    def validate_base_url(cls, base_url):
        if not base_url.startswith(("http://", "https://")):
            raise AgentException(ErrorEnum.BASE_URL_ERR)
        return base_url.rstrip("/")  # 去除末尾斜杠

    @classmethod
    @field_validator("api_key")
    def validate_api_key(cls, api_key):
        if not api_key:
            raise AgentException(ErrorEnum.NOT_FOUND_API_KEY)
        return api_key

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
        env_file=str(ENV_FILE),                # 指定 .env 文件
        env_file_encoding="utf-8",      # 文件编码
        case_sensitive=False,           # 环境变量名不区分大小写
        extra="ignore",                 # 忽略未定义的额外字段
        env_prefix="",                  # 无前缀（保持默认）
        validate_default=False,         # 不验证默认值（提升启动速度）
    )

# 全局变量，方便统一管理
settings = Setting()