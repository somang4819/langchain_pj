# pytest -v

import pytest
import httpx
from main import app

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
