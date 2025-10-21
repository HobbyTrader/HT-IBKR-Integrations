from ib_async import *
from constants import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID

ib = IB()
ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)

# Get account summary
account = ib.managedAccounts()[0]       # returns a list of account strings, usually only one element hence [0] index
summary = ib.accountSummary(account)    # Check AvailableFunds vs BuyingPower  
for item in summary:
    print(f"{item.tag}: {item.value}")

ib.disconnect()
