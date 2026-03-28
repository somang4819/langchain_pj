# 1. 체인 생성 (공통)
# 2. 지수 정보 가져오기 (공통)
# 3. 기업 정보 (공통), etf는 반복
# 4. 기업 정도 RAG입력 (공통), etf는 반복
# 5. 체인 호출

from models import *

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
    market: MarketIndicator = MarketIndicator()

    # 생성자 (객체 초기화)
    def model_post_init(self, __context):
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
    
    # def get_valuation_metrics(symbol):
    #     import yfinance as yf

    #     t = yf.Ticker(symbol)
    #     info = t.info
    #     fin = t.financials
    #     bal = t.balance_sheet
    #     # cf = t.cashflow

    #     # fcf = cf.loc["Free Cash Flow"].iloc[0]
    #     revenue = fin.loc["Total Revenue"]
    #     op_income = fin.loc["Operating Income"].iloc[0]

    #     revenue_growth = (revenue.iloc[0] - revenue.iloc[1]) / revenue.iloc[1]
    #     operating_margin = op_income / revenue.iloc[0]

    #     ev_ebitda = info.get("enterpriseToEbitda")

    #     return {
    #         # "fcf": fcf,
    #         "revenue_growth": revenue_growth,
    #         "operating_margin": operating_margin,
    #         "ev_ebitda": ev_ebitda,
    #     }