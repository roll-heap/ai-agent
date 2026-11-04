import re
import time
from datetime import datetime

import akshare as ak
import yfinance as yf

from agent.tool.model import StockPriceModel, StockInfoModel
from exception import AgentException


class StockDao:
    """股票数据访问层（支持 A股 + 美股）"""

    @staticmethod
    def _is_a_stock(code: str) -> bool:
        """判断是否为 A股（6位数字，或包含 .SH/.SZ）"""
        # 纯数字且长度为6
        if re.match(r'^\d{6}$', code):
            return True
        # 包含 .SH 或 .SZ
        if '.SH' in code.upper() or '.SZ' in code.upper():
            return True
        return False

    @staticmethod
    def _normalize_a_code(code: str) -> str:
        """标准化 A股代码"""
        # 如果已经包含 .SH/.SZ，直接返回
        if '.SH' in code.upper() or '.SZ' in code.upper():
            return code.upper()
        # 否则根据代码前缀判断市场
        if code.startswith('6'):
            return f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            return f"{code}.SZ"
        return code

    @staticmethod
    def get_price_a(code: str, max_retries:int=3) -> StockPriceModel:
        """获取 A股实时行情（akshare）"""
        """尝试多个数据源获取 A股行情"""
        sources = [
            ("东方财富", lambda: ak.stock_zh_a_spot_em()),
            ("新浪财经", lambda: ak.stock_zh_a_spot()),
        ]
        last_error = []
        for source_name, source_func in sources:
            for attempt in range(max_retries):
                try:
                    StockDao.__do_get_price_a(source_func, code)
                except Exception as e:
                    last_error.append(e)
                    print(f"⚠️ {source_name} 接口失败: {e}")
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt  # 2, 4, 8 秒
                        time.sleep(wait)
                    continue
        raise AgentException(f"查询 A股数据源均失败: {str(last_error)}")

    @staticmethod
    def __do_get_price_a(source_func, code):
        # 获取实时行情
        df = source_func()
        # 查找对应股票
        row = df[df['代码'] == code]
        if row.empty:
            # 尝试标准化代码后再查
            normalized = StockDao._normalize_a_code(code)
            # 提取纯数字代码
            pure_code = re.sub(r'[^0-9]', '', normalized)
            row = df[df['代码'] == pure_code]
            if row.empty:
                raise AgentException(f"未找到 A股代码: {code}")

        r = row.iloc[0]
        return StockPriceModel(
            code=str(r['代码']),
            name=str(r['名称']),
            price=float(r['最新价']) if r['最新价'] else 0.0,
            change=float(r['涨跌额']) if r['涨跌额'] else 0.0,
            change_percent=float(r['涨跌幅']) if r['涨跌幅'] else 0.0,
            volume=str(r['成交量']) if r['成交量'] else "N/A",
            amount=str(r['成交额']) if r['成交额'] else "N/A",
            turnover=float(r['换手率']) if r['换手率'] else None,
            pe_ratio=float(r['市盈率-动态']) if r['市盈率-动态'] else None,
            market_cap=str(r['总市值']) if r['总市值'] else "N/A",
            high=float(r['最高']) if r['最高'] else None,
            low=float(r['最低']) if r['最低'] else None,
            open_price=float(r['今开']) if r['今开'] else None,
            prev_close=float(r['昨收']) if r['昨收'] else None,
            market="A股",
            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    @staticmethod
    def get_price_us(code: str) -> StockPriceModel:
        """获取美股实时行情（yfinance）"""
        try:
            # 标准化美股代码
            ticker_symbol = code.upper()
            if not ticker_symbol.endswith('.SA') and not ticker_symbol.endswith('.HK'):
                # 美股通常直接使用代码
                pass

            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            if not info or 'currentPrice' not in info and 'regularMarketPrice' not in info:
                # 尝试用 history 获取
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise AgentException(f"未找到美股代码: {code}")
                price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                high = hist['High'].iloc[-1]
                low = hist['Low'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                prev_close = float(info.get('previousClose', price)) if info else price
            else:
                price = float(info.get('currentPrice') or info.get('regularMarketPrice', 0))
                open_price = float(info.get('regularMarketOpen', 0))
                high = float(info.get('regularMarketDayHigh', 0))
                low = float(info.get('regularMarketDayLow', 0))
                volume = info.get('regularMarketVolume', 'N/A')
                prev_close = float(info.get('previousClose', price))

            change = price - prev_close
            change_percent = (change / prev_close * 100) if prev_close != 0 else 0

            name = info.get('longName', info.get('shortName', code))

            return StockPriceModel(
                code=ticker_symbol,
                name=str(name),
                price=price,
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=str(volume) if volume else "N/A",
                amount="N/A",
                turnover=None,
                pe_ratio=float(info.get('trailingPE')) if info and info.get('trailingPE') else None,
                market_cap=info.get('marketCap') if info and info.get('marketCap') else "N/A",
                high=high,
                low=low,
                open_price=open_price,
                prev_close=prev_close,
                market="美股",
                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        except Exception as e:
            raise AgentException(f"查询美股失败: {str(e)}")

    @staticmethod
    def get_stock_price(code: str) -> StockPriceModel:
        """统一入口：自动判断 A股/美股"""
        if StockDao._is_a_stock(code):
            return StockDao.get_price_a(code)
        else:
            return StockDao.get_price_us(code)

    @staticmethod
    def get_stock_info(code: str) -> StockInfoModel:
        """获取股票基本面信息（主要针对美股）"""
        try:
            if StockDao._is_a_stock(code):
                # A股使用 akshare
                df = ak.stock_zh_a_spot_em()
                pure_code = re.sub(r'[^0-9]', '', code)
                row = df[df['代码'] == pure_code]
                if row.empty:
                    raise AgentException(f"未找到 A股: {code}")

                r = row.iloc[0]
                return StockInfoModel(
                    code=str(r['代码']),
                    name=str(r['名称']),
                    market="A股",
                    sector="N/A",
                    industry="N/A",
                    employees=None,
                    country="中国",
                    website=None,
                    business=None,
                    market_cap=str(r['总市值']) if r['总市值'] else "N/A",
                    pe_ratio=float(r['市盈率-动态']) if r['市盈率-动态'] else None,
                    eps=None,
                    dividend_yield=None,
                    beta=None,
                    high_52w=None,
                    low_52w=None,
                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            else:
                # 美股使用 yfinance
                ticker = yf.Ticker(code.upper())
                info = ticker.info

                if not info:
                    raise AgentException(f"未找到美股: {code}")

                return StockInfoModel(
                    code=code.upper(),
                    name=info.get('longName', info.get('shortName', code)),
                    market="美股",
                    sector=info.get('sector'),
                    industry=info.get('industry'),
                    employees=info.get('fullTimeEmployees'),
                    country=info.get('country'),
                    website=info.get('website'),
                    business=info.get('longBusinessSummary', ''),
                    market_cap=info.get('marketCap'),
                    pe_ratio=info.get('trailingPE'),
                    eps=info.get('trailingEps'),
                    dividend_yield=info.get('dividendYield') * 100 if info.get('dividendYield') else None,
                    beta=info.get('beta'),
                    high_52w=info.get('fiftyTwoWeekHigh'),
                    low_52w=info.get('fiftyTwoWeekLow'),
                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

        except Exception as e:
            raise AgentException(f"查询股票信息失败: {str(e)}")