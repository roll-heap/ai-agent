from agent.tool.dao import StockDao
from agent.tool.model import ToolResponseModel
from exception import AgentException


class StockService:
    @staticmethod
    def get_price(code: str) -> ToolResponseModel:
        """获取股票实时行情"""
        try:
            data = StockDao.get_stock_price(code)
            return ToolResponseModel(data=data.model_dump(mode="json"))
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))

    @staticmethod
    def get_info(code: str) -> ToolResponseModel:
        """获取股票基本面信息"""
        try:
            data = StockDao.get_stock_info(code)
            return ToolResponseModel(data=data.model_dump(mode="json"))
        except AgentException as e:
            return ToolResponseModel(success=False, msg=e.msg)
        except Exception as e:
            return ToolResponseModel(success=False, msg=str(e))