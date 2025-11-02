from ib_async import IB
from constants import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID

ib = IB()
ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
print("Connected to Trader Work Station or ib_gateway")
input("Press Enter to disconnect from ib_gateway...")

ib.disconnect()
