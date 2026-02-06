
from sqlalchemy.orm import Session
from data.database import init_db, Asset, FundamentalData

engine = init_db()
session = Session(engine)

ticker = 'AGXY3'
asset = session.query(Asset).filter_by(ticker=ticker).first()
if asset:
    fund = session.query(FundamentalData).filter_by(asset_id=asset.id).first()
    print(f"{ticker} Revenue Growth 5y: {fund.revenue_growth_5y}")
else:
    print(f"{ticker} not found")

session.close()
