from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.logger_core import log


class BaseApplication:
    """
    fastAPI 应用基类
    提供健康检查 + 启动/关闭钩子
    """
    def __init__(self, title: str, version: str, **kwargs):
        log.info("开始初始化BaseApplication")
        self.app = FastAPI(title=title, version=version, **kwargs)
        self._setup_health()
        self._setup_lifespan()

    def _setup_health(self):
        @asynccontextmanager
        async def health():
            return {"status":"health", "version": self.app.version}

    def _setup_lifespan(self):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.on_startup(app)
            yield
            await self.on_shutdown(app)
        self.app.router.lifespan_context = lifespan

    async def on_startup(self, app):
        pass

    async def on_shutdown(self, app):
        pass
