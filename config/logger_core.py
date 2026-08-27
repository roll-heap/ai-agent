from datetime import datetime
from functools import wraps
from uuid import uuid4

from logcore import get_logger, set_correlation_id

from config.config import settings, BASE_DIR


class Logger:
    @staticmethod
    def logger() -> "LogCoreLogger":
        """
        # log_path = Path(__file__).parent.parent / "log"
        # 在logcore中会创建文件夹
        # log_path.mkdir(parents=True, exist_ok=True)
        :return: LogCoreLogger
        """
        return get_logger(
            name=settings.app_name,                           # 日志记录器名称
            level=settings.log_level,                         # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
            # json=True,                                    # 是否输出 JSON 格式，False 输出人类可读格式
            file=BASE_DIR / settings.log_file,                # 可选：将日志输出到文件
            correlation_id="N/A",                           # 可选：设置一个全局关联ID,设置默认值
            max_file_size=10 * 1024 * 1024,                 # 单个日志文件最大10MB
            backup_count=5,                                 # 保留最近5个备份文件
            redact_fields={"password", "secret", "api_key"}, # 自动脱敏这些字段
            console = False,                                # 关闭控制台输出，输出到日志文件中
        )

    @staticmethod
    def generate_trace_id():
        trace_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4()).replace('-', '')}"
        if trace_id:
            set_correlation_id(trace_id)
        return trace_id

def trace(func):
    """
    自动注入 trace_id 的装饰器。
    用法：在需要追踪的函数上加上 @trace 即可。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        Logger.generate_trace_id()
        log.info(f"{func.__name__}开始执行")
        try:
            # 3. 执行原函数
            result = func(*args, **kwargs)
            log.info(f"{func.__name__} 执行结束")
            return result
        except Exception as e:
            log.exception(f"{func.__name__} 执行异常")
            raise
        finally:
            # 4. 自动清除 trace_id，避免污染下一个请求
            set_correlation_id(None)

    return wrapper

# 全局变量，方便统一管理
log = Logger.logger()