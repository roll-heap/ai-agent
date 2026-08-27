from datetime import datetime

class CurrentTime:
    @staticmethod
    def current_time() -> str:
        """
           获取当前日期和时间。
        """
        return datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
