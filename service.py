import asyncio
import logging
import traceback
from typing import Any
from operator import itemgetter

import yfinance as yf
import pandas as pd
from fredapi import Fred
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from etfpy import ETF

import langchain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from models import *
from config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def initchain():
    print(f"LangChain 버전: {langchain.__version__}")

    # 간단한 테스트
    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = llm.invoke("안녕하세요!")
        print(f"응답: {response.content}")
    except Exception as e:
        print(f"설정 오류: {e}")

class AnalyzeStockItemByOne:
    etf_client: Any = ETF

    def __init__(self, ticker: str = ""):
        self.ticker = ticker
        self.market = type('Market', (), {})()

    def model_post_init(self, __context):
        if self.ticker:
            self.get_market_indicators()

    def get_market_indicators(self):    # 야후 파이낸스 주요 지수 
        sp500 = yf.download("^GSPC", period="1y", interval="1d")
        vix = yf.download("^VIX", period="1y")
        usd_krw = yf.download("KRW=X", period="6mo", interval="1d")

        fred = Fred(api_key="7679fe95133779dd18e1cc61b0a16079")
        cpi = fred.get_series("cpiaucsl")

        self.market.sp500=sp500
        self.market.vix=vix
        self.market.cpi=cpi
        self.market.usd_krw=usd_krw
    
    def get_valuation_metrics_one(self, symbol):
        t = yf.Ticker(symbol)
        info = t.info
        fin = t.financials
        bal = t.balance_sheet
        # cf = t.cashflow

        revenue_growth = "0"
        operating_margin = "0"
        
        # 데이터가 존재하는지 확인 후 계산
        if not fin.empty and "Total Revenue" in fin.index:
            revenue = fin.loc["Total Revenue"]
            if len(revenue) >= 2 and revenue.iloc[1] != 0:
                revenue_growth = str((revenue.iloc[0] - revenue.iloc[1]) / revenue.iloc[1])
            
            if "Operating Income" in fin.index:
                op_income = fin.loc["Operating Income"].iloc[0]
                operating_margin = str(op_income / revenue.iloc[0]) if revenue.iloc[0] != 0 else "0"

        ev_ebitda = str(info.get("enterpriseToEbitda", "N/A"))

        # 계산된 수치들을 StockIndicator 모델의 str 타입에 맞게 변환하여 반환
        return
    
    def is_etf(self):
        """ticker가 ETF인지 확인"""
        info = yf.Ticker(self.ticker).info
        return info.get('quoteType') == 'ETF'

    def get_valuation_metrics_all(self):    
        # 1단계: ETF 여부 확인
        if not self.is_etf():
            return
        
        try:
            # 2단계: ETF 비중 정보 가져오기 
            # 기본 정보
            yf_obj = yf.Ticker("SPY")
            info = yf_obj.info
            
            print(f"ETF: {info.get('longName')}")
            print(f"Expense Ratio: {info.get('expenseRatio')}%")
            print(f"Market Cap: ${info.get('marketCap'):,.0f}")
            print("\n" + "="*70)
        except Exception as e:
            logger.error(f"Failed to fetch ETF data for {self.ticker}: {e}")
            return {"error": "ETF 데이터를 가져올 수 없습니다"}
    
    async def crawl_naver_etf_holdings(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto("https://m.stock.naver.com/worldstock/etf/SPY/total", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            try:
                # StockInfo_list__V96U6 클래스의 모든 ul 찾기
                ul_list = page.locator(".RatioBarInfo_list__A-U1F")
                ul_count = await ul_list.count()
                print(f"📊 발견된 ul 개수: {ul_count}\n")
                
                dataframes = []
                
                # 각 ul 요소를 순회
                for ul_index in range(ul_count):
                    ul_locator = ul_list.nth(ul_index)
                    li_elements = ul_locator.locator("li")
                    li_count = await li_elements.count()
                    
                    stock_info = []
                    
                    # 각 li에서 key-value 추출
                    for li_index in range(li_count):
                        li = li_elements.nth(li_index)
                        
                        # key 추출 (strong 태그)
                        key = await li.locator(".RatioBarInfo_name__3HmZS").text_content()
                        
                        # value 추출 (span 태그)
                        value = await li.locator(".RatioBarInfo_ratio__bw-p-").text_content()
                        
#                        if key and value:
#                            stockElm=StockIndicator(name=key,weight=value, ticker=self.get_ticker_from_name(key))
#                            self.stock_indicator_list.holdings.append(stockElm)
                
                print(self.stock_indicator_list)
            except Exception as e:
                print(f"❌ 에러: {e}")
                traceback.print_exc()
            
            await browser.close()

    async def crawl_naver_stockinfobyone_naver(self, db: AsyncSession):
        # 크롤링 키를 StockIndicator 필드명으로 매핑
        KEY_TO_FIELD_MAP = {
            "전일": "previous_close",
            "시가": "opening_price",
            "고가": "high_price",
            "저가": "low_price",
            "거래량": "volume",
            "대금": "trading_value",
            "시총": "market_cap",
            "NAV": "nav",
            "최근 1개월 수익률": "return_1m",
            "최근 3개월 수익률": "return_3m",
            "최근 6개월 수익률": "return_6m",
            "최근 1년 수익률": "return_1y",
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                page = await browser.new_page()
                
                # Use self.ticker for the URL
                await page.goto(f"https://m.stock.naver.com/domestic/stock/{self.ticker}/total", wait_until="networkidle")
                print(f"https://m.stock.naver.com/domestic/stock/{self.ticker}/total")
                await page.wait_for_timeout(500)
                
                scraped_data = {}
                ul_list = page.locator(".StockInfo_list__V96U6")
                ul_count = await ul_list.count()
                print(f"📊 발견된 ul 개수: {ul_count}\n")
                
                dataframes = []
                
                # 각 ul 요소를 순회
                for ul_index in range(ul_count):
                    ul_locator = ul_list.nth(ul_index)
                    li_elements = ul_locator.locator("li.StockInfo_item__puHWj")
                    li_count = await li_elements.count()
                    
                    stock_info = []
                    
                    # 각 li에서 key-value 추출
                    for li_index in range(li_count):
                        li = li_elements.nth(li_index)
                        
                        # key 추출 (strong 태그)
                        key = await li.locator(".StockInfo_key__naiA4").text_content()
                        
                        # value 추출 (span 태그)
                        value = await li.locator(".StockInfo_value__WAuXk").text_content()
                        
                        if key and value:
                            print(f"키: {key}, 값: {value}")
                            field_name = KEY_TO_FIELD_MAP.get(key)
                            if field_name:
                                scraped_data[field_name] = value

                stock_record = None
                if scraped_data:
                    # DB에서 해당 ticker 조회
                    stmt = select(StockIndicatorTable).where(StockIndicatorTable.ticker == self.ticker)
                    result = await db.execute(stmt)
                    stock_record = result.scalar_one_or_none()

                    if not stock_record:
                        # 없으면 새로 생성
                        stock_record = StockIndicatorTable(ticker=self.ticker)
                        db.add(stock_record)
                    
                    # 필드 업데이트 (있으면 업데이트, 없으면 신규 생성된 객체에 값 할당)
                    for field, val in scraped_data.items():
                        setattr(stock_record, field, val)
                    
                    await db.commit()
                    print(f" {self.ticker} 데이터 저장/업데이트 완료")

                return stock_record
            except Exception as e:
                print(f"❌ 에러: {e}")
                traceback.print_exc()
            finally:
                await browser.close()
            
    def get_ticker_from_name(self, stock_name):
        """
        stock name으로 ticker 찾기
        예: "NVIDIA CORP" → "NVDA"
        """
        try:
            # yfinance에서 직접 검색
            ticker_obj = yf.Ticker(stock_name)
            info = ticker_obj.info
            
            if 'symbol' in info:
                return info['symbol']
        except:
            pass
        
        return ""
    
    async def RAG_pipeline_domestic(self, item: StockIndicatorTable):
        settings = get_settings()

        # 야후 파이낸스 주요 지수 
        # yfinance download는 blocking I/O이므로 thread pool에서 실행하여 이벤트 루프 지연을 방지합니다.
        sp500_df = await asyncio.to_thread(yf.download, "^GSPC", period="5d", interval="1d")
        vix_df = await asyncio.to_thread(yf.download, "^VIX", period="5d")
        usd_krw_df = await asyncio.to_thread(yf.download, "KRW=X", period="5d", interval="1d")
        kospi_df = await asyncio.to_thread(yf.download, "^KS11", period="5d", interval="1d")
        kosdaq_df = await asyncio.to_thread(yf.download, "^KQ11", period="5d", interval="1d")

        sp500 = sp500_df.tail(1).to_string()
        vix = vix_df.tail(1).to_string()
        usd_krw = usd_krw_df.tail(1).to_string()
        kospi = kospi_df.tail(1).to_string()
        kosdaq = kosdaq_df.tail(1).to_string()
        
        print("야후 파이낸스 주요 지수 ")

        # Data Loader - 웹페이지 데이터 가져오기
        url = f"https://finance.naver.com/item/coinfo.naver?code={item.ticker}&target=finsum_more"
        loader = WebBaseLoader(url)

        # 웹페이지 텍스트 -> Documents
        # WebBaseLoader.aload()는 내부적으로 asyncio.run()을 호출하여 FastAPI 루프와 충돌할 수 있습니다.
        # 대신 load()를 thread에서 실행하여 안전하게 비동기 처리를 수행합니다.
        docs = await asyncio.to_thread(loader.load)

        # Text Split (Documents -> small chunks: Documents)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Indexing (Texts -> Embedding -> Store)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",  # 명시적 모델 지정
            api_key=settings.openai_api_key
        )        
        vectorstore = await asyncio.to_thread(
            Chroma.from_documents,
            documents=splits,
            embedding=embeddings
        )
        print("indexing")

        # 프롬프트 정의 
        prompt = ChatPromptTemplate.from_template("""
        다음 지표와 재무재표 정보를 기반으로 투자가치를 분석하라
        너는 보수적인 주식 트레이딩 분석가 워렌 버핏이다.
        반드시 매수(BUY), 매도(SELL), 보유(HOLD) 중 하나를 결정하라.

        규칙:
        - 금액, 수량, 계좌 관련 판단을 하지 마라
        - 출력 형식은 반드시 지정된 JSON 스키마를 따를 것
        - 이유는 한글로 작성

        참고 정보(Context):
        {context}

        지표:
        - sp500: {market_sp500}
        - vix : {market_vix}
        - usd_krw : {market_usd_krw}
        - kospi : {market_kospi}
        - kosdaq : {market_kosdaq}

        - previous_close : {item_previous_close}
        - opening_price : {item_opening_price}
        - high_price : {item_high_price}
        - low_price : {item_low_price}
        - volume : {item_volume}
        - trading_value : {item_trading_value}
        - nav : {item_nav}
        - market_cap : {item_market_cap}

        # 수익률 정보
        - return_1m : {item_return_1m}
        - return_3m : {item_return_3m}
        - return_6m : {item_return_6m}
        - return_1y : {item_return_1y}
        """)
        print("프롬프트 정의")

        # LLM
        llm = ChatOpenAI(
            model='gpt-4o',
            temperature=0,
            api_key=settings.openai_api_key  # openai_api_key → api_key
        )
        try:
            structured_llm = llm.with_structured_output(TradeDecision)
        except Exception as e:
            from langchain_core.output_parsers import JsonOutputParser
            parser = JsonOutputParser(pydantic_object=TradeDecision)
            structured_llm = llm | parser

        # Retrieval
        retriever = vectorstore.as_retriever(
            search_type='mmr',
            search_kwargs={'k': 3, 'lambda_mult': 0.15}
        )
        # Combine Documents
        def format_docs(docs):
            return '\n\n'.join(doc.page_content for doc in docs)
        
        print("쿼리 시도 ")

        # RAG Chain 연결
        rag_chain = (
            {
                "context": itemgetter("query") | retriever | format_docs,
                "market_sp500": itemgetter("market_sp500"),
                "market_vix": itemgetter("market_vix"),
                "market_usd_krw": itemgetter("market_usd_krw"),
                "market_kospi": itemgetter("market_kospi"),
                "market_kosdaq": itemgetter("market_kosdaq"),
                "item_previous_close": itemgetter("item_previous_close"),
                "item_opening_price": itemgetter("item_opening_price"),
                "item_high_price": itemgetter("item_high_price"),
                "item_low_price": itemgetter("item_low_price"),
                "item_volume": itemgetter("item_volume"),
                "item_trading_value": itemgetter("item_trading_value"),
                "item_nav": itemgetter("item_nav"),
                "item_market_cap": itemgetter("item_market_cap"),
                "item_return_1m": itemgetter("item_return_1m"),
                "item_return_3m": itemgetter("item_return_3m"),
                "item_return_6m": itemgetter("item_return_6m"),
                "item_return_1y": itemgetter("item_return_1y"),
            }
            | prompt
            | structured_llm
        )

        # ⭐ ainvoke 호출 (모든 필드값을 명시적으로 전달)
        result = await rag_chain.ainvoke({
            "query": "투자 판단해줘",
            "market_sp500": sp500,
            "market_vix": vix,
            "market_usd_krw": usd_krw,
            "market_kospi": kospi,
            "market_kosdaq": kosdaq,
            "item_previous_close": item.previous_close,
            "item_opening_price": item.opening_price,
            "item_high_price": item.high_price,
            "item_low_price": item.low_price,
            "item_volume": item.volume,
            "item_trading_value": item.trading_value,
            "item_nav": item.nav,
            "item_market_cap": item.market_cap,
            "item_return_1m": item.return_1m,
            "item_return_3m": item.return_3m,
            "item_return_6m": item.return_6m,
            "item_return_1y": item.return_1y,
        })

        print("쿼리 성공 ")
        print(result)
        return result