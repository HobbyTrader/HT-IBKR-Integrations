from dataclasses import dataclass
import argparse
import logging
import threading
import time

from app.services.execution import ExecutionService
from app.utils import load_config_scheduler
from app.utils.logger import LoggerManager
from app.utils.sqllitemanager import SQLiteManager

LoggerManager("EXECUTION_WATCHER")
logger = logging.getLogger(__name__)

_stop_event = threading.Event()

EXECUTION_WATCHER_CLIENT_ID_BASE = 1250000000
EXECUTION_WATCHER_CLIENT_ID_SPAN = 700000000


@dataclass(frozen=True)
class ExecutionWatcherArguments:
    client_id: int
    req_id: int


def generate_execution_watcher_client_id() -> int:
    timestamp_part = int(time.time_ns()) % 1000000
    return EXECUTION_WATCHER_CLIENT_ID_BASE + (timestamp_part % EXECUTION_WATCHER_CLIENT_ID_SPAN)


def get_arguments() -> ExecutionWatcherArguments:
    parser = argparse.ArgumentParser(description="Watch and persist IBKR executions")
    parser.add_argument("--client-id", type=int, default=None)
    parser.add_argument("--req-id", type=int, default=1)
    parsed = parser.parse_args()

    client_id = parsed.client_id
    if client_id is None:
        client_id = generate_execution_watcher_client_id()

    return ExecutionWatcherArguments(
        client_id=client_id,
        req_id=parsed.req_id,
    )


def scheduler_stop() -> None:
    logger.info("Execution watcher stop requested.")
    _stop_event.set()


def ensure_executions_table() -> None:
    manager = SQLiteManager()
    try:
        if manager.table_exists("executions"):
            logger.info("Table executions already exists.")
            return

        logger.info("Table executions is missing. Initializing tables from table definitions.")
        manager.initialize_tables()
    finally:
        manager.close()


def main() -> None:
    args = get_arguments()
    logger.info("Execution watcher started with clientId=%s reqId=%s", args.client_id, args.req_id)

    with ExecutionService(clientId=args.client_id) as execution_service:
        execution_service.get_executions(reqId=args.req_id)

    logger.info("Execution watcher completed reqExecutions refresh for reqId=%s.", args.req_id)


def run_scheduler() -> None:
    ensure_executions_table()

    config_scheduler_execution = load_config_scheduler().get("execution_watcher", {})
    logger.info("Loaded scheduler configuration for execution watcher: %s", config_scheduler_execution)

    if not config_scheduler_execution.get("enabled", False):
        logger.info("Execution watcher scheduler is disabled in configuration. Only 1 execution will be performed.")
        main()
        scheduler_stop()
        return

    interval = config_scheduler_execution.get("interval", 300)
    logger.info("Starting execution watcher scheduler with interval %s seconds.", interval)

    while not _stop_event.is_set():
        main()
        if _stop_event.is_set():
            break
        logger.info("Execution watcher scheduler sleeping for %s seconds...", interval)
        _stop_event.wait(interval)


if __name__ == "__main__":
    run_scheduler()