# uvicorn main:app --reload --port 8000

from fastapi import FastAPI, Depends
from typing import List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from service import *
from database import engine, get_db
from config import get_settings
from models import *
import logging

logger = logging.getLogger(__name__)

settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 준비 중...")
    initchain()

    # 테이블 자동 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    print("서버 종료 중...")

app = FastAPI(lifespan=lifespan)

class Item(BaseModel):
    code: str

@app.get("/")
def read_root():
    return {"version": settings.api_version}

@app.post("/items/")
async def create_item(item: Item):
    return item

@app.post("/analyze-stock-items/")
async def analyze_stock_items(items: List[StockItem], db: AsyncSession = Depends(get_db)):
    results = []
    for item in items:
        # 요청받은 ticker를 사용하여 데이터 가져오기 
        analyzer = AnalyzeStockItemByOne(ticker=item.ticker)
        infos = await analyzer.crawl_naver_stockinfobyone_naver(db)
        if infos:
            res = await analyzer.RAG_pipeline_domestic(infos)
            results.append({"ticker": item.ticker, "analysis": res})
    
    return results
