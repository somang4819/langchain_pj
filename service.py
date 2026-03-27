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
    market: MarketIndicator

    # 생성자 (객체 초기화)
    def __init__(self):
        self.get_market_indicators()

    def get_market_indicators(self):    # 야후 파이낸스 주요 지수 
        import yfinance as yf
        from fredapi import Fred

        sp500 = yf.download("^GSPC", period="1y", interval="1d")
        vix = yf.download("^VIX", period="1y")
        usd_krw = yf.download("KRW=X", period="6mo", interval="1d")

        fred = Fred(api_key="7679fe95133779dd18e1cc61b0a16079")
        cpi = fred.get_series("cpiaucsl")

        return MarketIndicator(
            sp500=sp500,
            vix=vix,
            cpi=cpi,
            usd_krw=usd_krw,
        )