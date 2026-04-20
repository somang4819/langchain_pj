from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import pandas as pd

class StockItem(BaseModel):
    name: str
    ticker: str = ""
    quantity: str 
    value: str
    type: str
    is_etf: str
    recommendation: str

class StockIndicator(BaseModel):
    name: str
    ticker: str = ""
    revenue_growth: str = "0"
    operating_margin: str ="0"
    ev_ebitda: str = "N/A"
    weight: str = "0"               # 구성 종목의 비중

    # 가격 정보 
    previous_close: str = "0"                   # 전일
    opening_price: str = "0"                    # 시가
    high_price: str = "0"                       # 고가
    low_price: str = "0"                        # 저가
    volume: str = "0"                           # 거래량
    trading_value: str = "0"                    # 대금
    nav: str = "0"                              # NAV
    market_cap: str = "0"                       # 시가총액
    
    # 수익률 정보
    return_1m: str = "0"                        # 최근 1개월 수익률
    return_3m: str = "0"                        # 최근 3개월 수익률
    return_6m: str = "0"                        # 최근 6개월 수익률
    return_1y: str = "0"                        # 최근 1년 수익률

class StockIndicatorList(BaseModel):
    name: str
    ticker: str
    holdings: List[StockIndicator]      # 여러 종목을 담는 리스트  ETF

class StockInfo(BaseModel):
    previous_close: str  # 전일
    opening_price: str   # 시가
    high_price: str      # 고가
    low_price: str       # 저가
    volume: str          # 거래량
    trading_value: str   # 대금
    nav: str             # NAV
    return_1m: str       # 최근 1개월 수익률
    return_3m: str       # 최근 3개월 수익률
    return_6m: str       # 최근 6개월 수익률
    return_1y: str       # 최근 1년 수익률
    market_cap: str      # 시가총액

class MarketIndicator(BaseModel):
    sp500: Optional[pd.DataFrame] = None
    vix: Optional[pd.DataFrame] = None
    cpi: Optional[pd.Series] = None
    usd_krw: Optional[pd.DataFrame] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

