# 1. 체인 생성 (공통)
# 2. 지수 정보 가져오기 (공통)
# 3. 기업 정보 (공통), etf는 반복
# 4. 기업 정도 RAG입력 (공통), etf는 반복
# 5. 체인 호출

from yfinance import ticker

from models import *
from etfpy import ETF
from typing import Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def initchain():
    # 버전 확인
    import langchain
    from langchain_openai import ChatOpenAI

    print(f"LangChain 버전: {langchain.__version__}")

    # 간단한 테스트
    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = llm.invoke("안녕하세요!")
        print(f"응답: {response.content}")
    except Exception as e:
        print(f"설정 오류: {e}")

class AnalyzeStockItemByOne(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    market: MarketIndicator = MarketIndicator()
    stock_indicator_list: StockIndicatorList = StockIndicatorList(name="", ticker="", holdings=[]) 
    ticker: str = "" 
    etf_client: Any = ETF

    # 생성자 (객체 초기화)
    def model_post_init(self, __context):
        if self.ticker:
            self.get_market_indicators()

    def get_market_indicators(self):    # 야후 파이낸스 주요 지수 
        import yfinance as yf
        from fredapi import Fred

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
        import yfinance as yf

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
        return StockIndicator(
            name=info.get("longName", symbol),
            ticker=symbol,
            revenue_growth=revenue_growth,
            operating_margin=operating_margin,
            ev_ebitda=ev_ebitda,
            weight="0"  # 가중치는 추후 계산 로직에 따라 설정
        )
    
    def is_etf(self):
        """ticker가 ETF인지 확인"""
        import yfinance as yf
        
        info = yf.Ticker(self.ticker).info
        return info.get('quoteType') == 'ETF'

    def get_valuation_metrics_all(self):    
        # 1단계: ETF 여부 확인
        if not self.is_etf():
            return StockIndicatorList(
                name="",
                ticker=self.ticker,
                holdings=[]
            )
        
        try:
            # 2단계: ETF 비중 정보 가져오기 
            import yfinance as yf
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

        return StockIndicatorList(
            name=self.ticker,
            ticker=self.ticker,
            holdings=[]
        )
    
    async def crawl_naver_etf_holdings(self):
        from playwright.async_api import async_playwright
        import pandas as pd

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
                        
                        if key and value:
                            stockElm=StockIndicator(name=key,weight=value, ticker=self.get_ticker_from_name(key))
                            self.stock_indicator_list.holdings.append(stockElm)
                
                print(self.stock_indicator_list)
            except Exception as e:
                print(f"❌ 에러: {e}")
                import traceback
                traceback.print_exc()
            
            await browser.close()

    async def crawl_naver_stockinfobyone(self, stockinfo: StockIndicator):
        from playwright.async_api import async_playwright
        import pandas as pd

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
            page = await browser.new_page()
            
            await page.goto(f"https://m.stock.naver.com/domestic/stock/{stockinfo.ticker}/total", wait_until="networkidle")
            await page.wait_for_timeout(500)
            
            try:
                # StockInfo_list__V96U6 클래스의 모든 ul 찾기
                ul_list = page.locator(".StockInfo_article__iOMzt StockInfo_isActive__xK9e1")
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
                        key = await li.locator(".StockInfo_key__naiA4").text_content()
                        
                        # value 추출 (span 태그)
                        value = await li.locator(".StockInfo_value__WAuXk").text_content()
                        
                        if key and value:
                            print(f"키: {key}, 값: {value}")
                            field_name = KEY_TO_FIELD_MAP.get(key)
                            if field_name:
                                setattr(stockinfo, field_name, value)
                            
                            #stockElm=StockIndicator(name=key,weight=value, ticker=self.get_ticker_from_name(key))
                            #self.stock_indicator_list.holdings.append(stockElm)
                print(stockinfo)
            except Exception as e:
                print(f"❌ 에러: {e}")
                import traceback
                traceback.print_exc()
            
            await browser.close()

    def get_ticker_from_name(self, stock_name):
        import yfinance as yf

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