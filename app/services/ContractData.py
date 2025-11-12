from app.dto.config import load_config

class ContractDataService:
    def __init__(self, logger):
        conf = load_config()
        logger.info("ContractDataService initialized")

    def contractDataDetails(self, reqId, contractDetails):
        attrs = vars(contractDetails)
        print(f"ContractDataDetails. ReqId: {reqId}, Details: {attrs}")

    def contractDataDetailsEnd(self, reqId):
        print(f"ContractDataDetailsEnd. ReqId: {reqId}")