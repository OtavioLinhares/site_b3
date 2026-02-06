
from sqlalchemy.orm import Session
from data.database import init_db, Asset, FundamentalData
import pandas as pd

engine = init_db()
session = Session(engine)

# Fetch top 5 by market cap to verify data
results = session.query(Asset.ticker, FundamentalData.market_cap).\
    join(Asset).\
    order_by(FundamentalData.market_cap.desc()).\
    limit(5).all()

print("Top 5 Market Cap:")
for ticker, mcap in results:
    print(f"{ticker}: {mcap}")

# Check count of non-null market caps
count = session.query(FundamentalData).filter(FundamentalData.market_cap != None).count()
print(f"\nTotal records with Market Cap: {count}")

session.close()
