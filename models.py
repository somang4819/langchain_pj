from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 부모 테이블: StockIndicatorList (예: ETF 정보)
class StockIndicatorListTable(Base):
    __tablename__ = "stock_indicator_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ticker = Column(String(20), nullable=False, unique=True)

    # 자식 테이블과의 관계 설정 (Back-reference)
    holdings = relationship("StockIndicatorTable", back_populates="parent_list", cascade="all, delete-orphan")


# 자식 테이블: StockIndicator (예: 구성 종목 상세)
class StockIndicatorTable(Base):
    __tablename__ = "stock_indicators"

    id = Column(Integer, primary_key=True, index=True)
    
    # 외래 키: 어떤 리스트에 속해있는지 식별
    list_id = Column(Integer, ForeignKey("stock_indicator_lists.id"))
    
    name = Column(String(100))
    ticker = Column(String(20))
    weight = Column(String(20), default="0")

    # 가격 정보
    previous_close = Column(String(50), default="0")
    opening_price = Column(String(50), default="0")
    high_price = Column(String(50), default="0")
    low_price = Column(String(50), default="0")
    volume = Column(String(50), default="0")
    trading_value = Column(String(50), default="0")
    nav = Column(String(50), default="0")
    market_cap = Column(String(50), default="0")

    # 수익률 정보
    return_1m = Column(String(20), default="0")
    return_3m = Column(String(20), default="0")
    return_6m = Column(String(20), default="0")
    return_1y = Column(String(20), default="0")

    # 관계 설정
    parent_list = relationship("StockIndicatorListTable", back_populates="holdings")