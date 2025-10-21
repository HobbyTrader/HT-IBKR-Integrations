import sys
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ib_async import *
from constants import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID

# Check if ticker symbol is passed or use AAPL as default
symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
loca_tz = ZoneInfo("America/New_York")      # Timezone for US markets
ib = IB()
ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)

back_days = 365
dt = ''
bars_list = []
contract = Stock(symbol, 'SMART', 'USD')

# Loop through weeks (5 day intervals) going backwards using endDateTime
while (dt =='') or ((dt + timedelta(days=back_days)) > datetime.now(loca_tz)):
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=dt,
        durationStr='5 D',
        barSizeSetting='1 min',
        whatToShow='TRADES',
        useRTH=False,                   # extended trading hours (not RTH Regular Trading Hours)
        formatDate=1)                   # use string formatted datetimes
    if not bars:
        break
    bars_list.append(bars)
    dt = bars[0].date
    print(dt)

# save to CSV file (not the most efficient code, it may fail after many minutes and loose your downloaded data)
all_bars = [b for bars in reversed(bars_list) for b in bars]
df = util.df(all_bars)
df.to_csv(f"DATA/{contract.symbol}.csv", index=False)

ib.disconnect()