from agent.tool.dao.date_current_dao import CurrentTimeDao


class CurrentTimeService:
    @staticmethod
    def current_time() -> dict:
        """
           获取当前日期和时间。
        """
        try:
            current_time = CurrentTimeDao.current_time()
            return {
                "success": True,
                "data": current_time
            }
        except Exception as e:
            return {
                "success": False,
                "data": str(e)
            }
