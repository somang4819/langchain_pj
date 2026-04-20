# pytest -v

import pytest
import httpx
from main import app
from unittest.mock import patch, MagicMock
from service import AnalyzeStockItemByOne
import pandas as pd


@pytest.mark.asyncio
async def test_create_stock_items_async():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        items = [
            {
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "quantity": "100",
                "value": "150.00",
                "type": "Tech",
                "recommendation": "Buy",
                "is_etf" : "n"
            },
            {
                "name": "Google",
                "ticker": "GOOGL",
                "quantity": "50",
                "value": "2800.00",
                "type": "Tech",
                "recommendation": "Hold",
                "is_etf" : "n"
            }
        ]
        response = await ac.post("/analyze-stock-items/", json=items)

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 2
    assert data["items"][0]["name"] == "Apple Inc."

def test_get_valuation_metrics_one( ):
    # 2. Act (함수 실행)
    analyzer = AnalyzeStockItemByOne(ticker="SPY")
    result = analyzer.get_valuation_metrics_one("AAPL")

    assert isinstance(result.revenue_growth, str)
    assert isinstance(result.operating_margin, str)
    assert isinstance(result.ev_ebitda, str)

@patch("service.ETF")    
def test_get_valuation_metrics_all(mock_etf):
    import asyncio

    mock_instance = MagicMock() 
    mock_instance.holdings = [] 
    mock_etf.return_value = mock_instance

    analyzer = AnalyzeStockItemByOne(ticker="SPY")
    asyncio.run(analyzer.crawl_naver())

