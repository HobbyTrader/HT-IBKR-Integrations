from ibapi.wrapper import EWrapper
from ibapi.client import *

class IBApi(EClient, EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

    def nextValidId(self, orderId: int):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId  