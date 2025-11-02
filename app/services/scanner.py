import logging

from app.core.ibapi import IBApi

from ibapi.wrapper import EWrapper
from ibapi.client import *
from ibapi.utils import iswrapper

class ScannerService(IBApi):
    def __init__(self) :
    # def __init__(self, scanner_repository):
        super().__init__()
        print("Scanner initialzed")
        # self.scanner_repository = scanner_repository

    # def get_scanner_data(self, criteria):
    #     return self.scanner_repository.fetch_data(criteria)

    # def save_scanner_data(self, data):
    #     print(f"Saving scanner data: {data}")
    #     return self.scanner_repository.store_data(data)
    @iswrapper
    def nextValidId(self, orderId: int):
        # Override to add subclass-specific logic and still call base version
        super().nextValidId(orderId)
        print(f"[ScannerService] Received nextValidId: {orderId} - requesting scanner parameters")

    @iswrapper
    def nextId(self):
        super().nextId(self)
        print(f"[ScannerService] Call to nextId")

    @iswrapper
    def scannerParameters(self, xml: str):
        logging.info("ScannerParameters received.")
        print("ScannerParameters received.")
        open('log/scanner.xml', 'w').write(xml)

    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(1)

    def get_scannerResult(self, scannerSubscription, filterTagValues):
        self.reqScannerSubscription(self.nextId(), scannerSubscription, [], filterTagvalues)
        time.sleep(1)

    