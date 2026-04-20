# uvicorn main:app --reload --port 8000

from fastapi import FastAPI, Depends
from typing import List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from service import *
from database import engine, get_db
from config import get_settings
from models import *

settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 준비 중...")
    initchain()

    yield
    print("서버 종료 중...")

app = FastAPI(lifespan=lifespan)

# 테이블 자동 생성
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class Item(BaseModel):
    code: str

@app.get("/")
def read_root():
    return {"version": settings.api_version}

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.post("/analyze-stock-items/")
async def create_stock_items():
    import asyncio
    # 종목 당 분석 수행Y

    analyzer = AnalyzeStockItemByOne()
    #analyzer.get_valuation_metrics_all()
    #await analyzer.crawl_naver_etf_holdings()
    await analyzer.crawl_naver_stockinfobyone()

    return {}