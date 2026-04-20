# uvicorn main:app --reload --port 8000

from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from models import StockItem
from contextlib import asynccontextmanager
from service import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 준비 중...")
    initchain()

    yield
    print("서버 종료 중...")

app = FastAPI(lifespan=lifespan)

class Item(BaseModel):
    code: str

@app.get("/")
def read_root():
    return {"test": "fastapi !!!"}

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.post("/analyze-stock-items/")
async def create_stock_items(items: List[StockItem]):
    import asyncio
    # 종목 당 분석 수행Y

    analyzer = AnalyzeStockItemByOne(ticker="SPY")
    #analyzer.get_valuation_metrics_all()
    #await analyzer.crawl_naver_etf_holdings()
    await analyzer.crawl_naver_stockinfobyone(StockIndicator(name="삼성전자", ticker="005930"))

    return {"received": len(items), "items": items}