from typing import Optional

from pydantic import BaseModel, Field


class StockPriceModel(BaseModel):
    """股票实时行情模型"""
    code: str = Field(description="股票代码")
    name: str = Field(description="股票名称")
    price: float = Field(description="当前价格")
    change: float = Field(description="涨跌额")
    change_percent: float = Field(description="涨跌幅（%）")
    volume: Optional[str] = Field(default="N/A", description="成交量")
    amount: Optional[str] = Field(default="N/A", description="成交额")
    turnover: Optional[float] = Field(default=None, description="换手率（%）")
    pe_ratio: Optional[float] = Field(default=None, description="市盈率")
    market_cap: Optional[str] = Field(default="N/A", description="总市值")
    high: Optional[float] = Field(default=None, description="今日最高价")
    low: Optional[float] = Field(default=None, description="今日最低价")
    open_price: Optional[float] = Field(default=None, description="今日开盘价")
    prev_close: Optional[float] = Field(default=None, description="昨日收盘价")
    market: str = Field(description="市场：A股/港股/美股")
    update_time: str = Field(description="数据更新时间")


class StockInfoModel(BaseModel):
    """股票基本面信息模型"""
    code: str = Field(description="股票代码")
    name: str = Field(description="公司名称")
    market: str = Field(description="市场")
    sector: Optional[str] = Field(default=None, description="所属行业")
    industry: Optional[str] = Field(default=None, description="细分行业")
    employees: Optional[int] = Field(default=None, description="员工人数")
    country: Optional[str] = Field(default=None, description="国家/地区")
    website: Optional[str] = Field(default=None, description="公司官网")
    business: Optional[str] = Field(default=None, description="主营业务")
    market_cap: Optional[str] = Field(default=None, description="总市值")
    pe_ratio: Optional[float] = Field(default=None, description="市盈率")
    eps: Optional[float] = Field(default=None, description="每股收益")
    dividend_yield: Optional[float] = Field(default=None, description="股息率（%）")
    beta: Optional[float] = Field(default=None, description="Beta系数")
    high_52w: Optional[float] = Field(default=None, description="52周最高")
    low_52w: Optional[float] = Field(default=None, description="52周最低")
    update_time: str = Field(description="数据更新时间")