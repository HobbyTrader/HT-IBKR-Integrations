from ib_async import *
from constants import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID

ib = IB()
ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)

# Two ways of getting the account summary
accounts = ib.managedAccounts()         # returns a list of account strings, usually only one element hence [0]
# accounts = ib.client.getAccounts()    # returns a list of account strings, usually only one element hence [0]

for account in accounts:
    print(f"Account: {account}")


ib.disconnect()
