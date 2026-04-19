from dataclasses import dataclass
import logging
import sys
from time import time
from typing import List

from app.dto.market_order_dto import MarketOrderDTO
from app.dto.strategy_dto import StrategyDTO
from app.services.order import OrderService
from app.services.position import PositionService
from app.utils.logger import LoggerManager
from ibapi.contract import Contract

LoggerManager("CLOSE_POSITIONS")
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ClosePosiotionsArguments:
    strategy_id: int
    
def get_arguments() -> ClosePosiotionsArguments:
    if len(sys.argv) > 1:
        logger.info(f"Starting with arguments: STRATEGY_ID = {sys.argv[1]}")
        strategy_id = int(sys.argv[1])
    else:
        strategy_id = None
    
    return ClosePosiotionsArguments(strategy_id=strategy_id)

def close_position_from_strategy(strategy_id: int):
    strategy_dto = StrategyDTO()
    market_order_dto = MarketOrderDTO()
    open_positions = []
    
    # args = get_arguments()
    # strategy = strategy_dto.get_strategy_by_id(args.strategy_id)
    strategy = strategy_dto.get_strategy_by_id(strategy_id)
    if not strategy:
        logger.error(f"Strategy with ID {strategy_id} not found. Exiting.")
        return
    
    if not strategy.is_market_open_now():
        logger.info(f"Market is closed for strategy {strategy.name}. Can't close positions now.")
        return
    
    # Retrieve all open positios on the IBKR account
    with PositionService() as position_serv:
        open_positions = position_serv.get_open_positions()
        logger.info(f"Found {len(open_positions)} open positions.")
    
    # Cancel all active orders and close/sell all open positions
    # Get Orders from database to retrive the ID' base on contract_id and today's orders
    if open_positions:
        for contract in open_positions:
            logger.info(f"Closing position for contract: {contract.symbol}, SecType: {contract.secType}, Exchange: {contract.exchange}, ContractID: {contract.conId}")
            # Implement the logic to close/sell the position here
            # This may involve creating and submitting market orders via IBKR API
            orders_to_cancel = market_order_dto.get_market_orders_by_contract_id_today(contract.conId)
            logger.info(f"Found {len(orders_to_cancel)} active orders to cancel for contract: {contract.symbol}.")
            for order in orders_to_cancel:
                with OrderService() as order_serv:
                    order_serv.cancel_order_by_id(order.order_id)
                    market_order_dto.update_market_order_status(order.order_id, "CANCELLED")
                    logger.info(f"Order ID: {order.order_id} cancelled for contract: {contract.symbol}.")
                    
                    order_serv.sell_open_position(contract, order.order_quantity, strategy.id)
                    logger.info(f"Sell order placed for contract ID: {contract.conId}, Quantity: {order.order_quantity}")
    else:
        logger.info("No open positions to close.")
    
    
        
if __name__ == "__main__":
    args = get_arguments()
    close_position_from_strategy(args.strategy_id)