from pydantic import BaseModel,ConfigDict
from typing import List, Optional
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
    sp500: Optional[pd.DataFrame] = None
    vix: Optional[pd.DataFrame] = None
    cpi: Optional[pd.Series] = None
    usd_krw: Optional[pd.DataFrame] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

