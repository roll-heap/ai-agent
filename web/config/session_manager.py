class SessionManager:
    """会话管理器（内存版）"""

    def __init__(self):
        self._session: dict[str, list] = {}

    def get_history(self, session_id: str) -> list:
        if session_id not in self._session:
            self._session[session_id] = []
        return self._session[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        self.get_history(session_id).append({"role": role, "content": content})

    def clear(self, session_id: str):
        if session_id in self._session:
            self._session[session_id] = []


# 全局会话管理器
session_manager = SessionManager()