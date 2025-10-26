
import sys
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from ib_async import *
from constants import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID

# Check if ticker symbol is passed or use AAPL as default
symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
loca_tz = ZoneInfo("America/New_York")      # Timezone for US markets

ib = IB()
ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)

contract = Stock(symbol, "SMART", "USD")                    # Step 1 : Define a contract object for which to fetch data (stocks in this case)

bars = ib.reqHistoricalData(                                # Step 2 : request historical data for the last day in 1 minute bars (limitations apply, 1 minute => about 1 month)
    contract,
    endDateTime="",
    durationStr="1 D",
    barSizeSetting="1 min",
    whatToShow="TRADES",
    useRTH=False,                       # When useRTH is False, get Extended Hours and PreMarket data
    formatDate=1                        # use string formatted datetimes
)

df = util.df(bars)
print(df.tail(5))
df.to_csv(f"DATA/{symbol}_1min_{datetime.now(loca_tz).strftime('%Y%m%d--%H-%M')}.csv", index=False)

ib.disconnect()
