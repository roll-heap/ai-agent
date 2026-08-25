from pathlib import Path

from pydantic import Field, field_validator
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    app_name:str=Field(default="weather-agent", alias="APP_NAME")

    # logger
    log_level:str=Field(default="INFO", alias="LOGGER_LEVEL")
    log_file:str=Field(default="", alias="LOGGER_NAME")
    # 天气
    query_weather_url:str = Field(default="", alias="QUERY_WEATHER_URL")
    query_weather_timeout:int = Field(default=0, alias="QUERY_WEATHER_TIMEOUT")

    #deepseek
    model:str = Field(default="", alias="MODEL")
    api_key:SecretStr = Field(..., alias="API_KEY")
    base_url: str = Field(default="https://api.deepseek.com", alias="BASE_URL")
    temperature: int = Field(default=0, alias="TEMPERATURE")
    timeout: int = Field(default=30, alias="TIMEOUT")
    max_retries: int = Field(default=2, alias="MAX_RETRIES")


    @classmethod
    @field_validator("base_url")
    def validate_base_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url 必须以 http:// 或 https:// 开头")
        return v.rstrip("/")  # 去除末尾斜杠



    # class Config:
    #     """
    #     pydantic框架里面约定的必须存在的
    #     """
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     case_sensitive = False
    #     extra = "ignore"  # 忽略未定义的变量
    # ============================================================
    # 5. 新版配置（替代 class Config）必须用model_config接收，因为Settings继承了BaseSettings
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),                 # 指定 .env 文件
        env_file_encoding="utf-8",              # 文件编码
        case_sensitive=False,                   # 环境变量名不区分大小写
        extra="ignore",                         # 忽略未定义的额外字段
        env_prefix="",                          # 无前缀（保持默认）
        validate_default=False,                 # 不验证默认值（提升启动速度）
    )

config = Settings()