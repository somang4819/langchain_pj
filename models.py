from pydantic import BaseModel
from typing import List
import pandas as pd

class StockItem(BaseModel):
    name: str
    ticker: str
    quantity: str
    value: str
    type: str
    is_etf: str
    recommendation: str

class StockIndicator(BaseModel):
    name: str
    ticker: str
    revenue_growth: str
    operating_margin: str
    ev_ebitda: str

class ETFIndicator(BaseModel):
    name: str
    ticker: str
    holdings: List[StockIndicator]   # 여러 종목을 담는 리스트

class MarketIndicator(BaseModel):
    sp500: pd.DataFrame
    vix: pd.DataFrame
    cpi: pd.Series
    usd_krw: pd.DataFrame

    # arbitrary_types_allowed 옵션, Pydantic이 Pandas 객체를 검증 없이 받아들임.
    class Config:
        arbitrary_types_allowed = True

