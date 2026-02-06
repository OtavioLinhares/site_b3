
from sqlalchemy.orm import Session
from data.database import init_db, Asset, FundamentalData

engine = init_db()
session = Session(engine)

ticker = 'PETR4'
asset = session.query(Asset).filter_by(ticker=ticker).first()
if asset:
    fund = session.query(FundamentalData).filter_by(asset_id=asset.id).first()
    print(f"{ticker} Liquidity 2m: {fund.liq_2m}")
else:
    print(f"{ticker} not found")

session.close()
