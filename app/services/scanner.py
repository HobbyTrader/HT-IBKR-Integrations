import logging
import time

from app.core.ibapi import IBApi

from ibapi.wrapper import EWrapper
from ibapi.client import *
from ibapi.utils import iswrapper

class ScannerService(IBApi):
    def __init__(self, config) :
    # def __init__(self, scanner_repository):
        super().__init__(config)
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

    # @iswrapper
    # def nextId(self):
    #     super().nextId(self)
    #     print(f"[ScannerService] Call to nextId")

    @iswrapper
    def scannerParameters(self, xml: str):
        logging.info("ScannerParameters received.")
        print("ScannerParameters received.")
        open('log/scanner.xml', 'w').write(xml)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        print("Scanner Data received")
        logging.info(f"scannerData. reqId: {reqId}, rank: {rank}, contractDetails: {contractDetails}, distance: {distance}, benchmark: {benchmark}, projection: {projection}, legsStr: {legsStr}.")

    def get_parameters(self):
        self.reqScannerParameters()
        time.sleep(5)

    def get_scannerResult(self, scannerSubscription, scannerOptions, filterTagValues):
        self.reqScannerSubscription(self.nextId(), scannerSubscription, scannerOptions, filterTagValues)
        time.sleep(10)

    