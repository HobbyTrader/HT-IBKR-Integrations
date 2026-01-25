#!/usr/bin/env python3
"""
run_between_times.py

Template to run a job repeatedly using the `schedule` library between 09:00 and 15:00.
Includes:
 - time-window guarding (local system time)
 - internal "exit" condition inside your job to stop the scheduler early
 - graceful shutdown on SIGINT/SIGTERM

Install dependency:
    pip install schedule
"""

import schedule
import time
import datetime
import logging
import signal
import sys
import os
from threading import Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Configurable parameters
START_HOUR = 9    # 09:00 local time (inclusive)
END_HOUR = 15     # 15:00 local time (exclusive) -> stops at or after 15:00
INTERVAL_SECONDS = 60  # how often to run job (use small number for testing)

# Internal control
_stop_event = Event()


def now_time():
    """Return current local time as a datetime.time object."""
    return datetime.datetime.now().time()

def within_window(start_hour=START_HOUR, end_hour=END_HOUR):
    """Return True if current local time is inside the configured window."""
    t = now_time()
    start = datetime.time(hour=start_hour, minute=0, second=0)
    end = datetime.time(hour=end_hour, minute=0, second=0)
    # Handles simple case where start < end on same day (9 < 15)
    return start <= t < end

def check_exit_condition() -> bool:
    """
    Replace this with your real exit condition.

    Return True to request that the whole runner stops immediately.
    Example placeholder behaviors:
      - exit if a sentinel file exists (e.g., 'STOP')
      - exit if some external flag/state is reached
    """
    # Example 1: sentinel file
    if os.path.exists("STOP"):
        logging.info("Exit condition met: 'STOP' file found.")
        return True

    # Example 2: custom logic placeholder
    # my_state = read_state_from_db()
    # if my_state == "done":
    #     return True

    return False


def main_task():
    """
    The actual work you want to run repeatedly.
    Return True to request exit (stop the scheduler and exit process).
    """
    logging.info("Starting main_task()")
    try:
        # -------------------------
        # Place your real work here
        # -------------------------
        # Example placeholder:
        # result = do_some_processing()
        # logging.info(f"Processed result: {result}")
        # -------------------------

        # After doing work, check the internal exit condition
        if check_exit_condition():
            return True

        # If you need to abort due to an exception you can also request exit:
        # raise SomeException("fatal failure")  # optionally catch below

        logging.info("main_task() finished normally.")
        return False

    except Exception as exc:
        logging.exception("Unhandled exception in main_task(): %s", exc)
        # Decide if an exception should stop the runner:
        return True


def job_wrapper():
    """
    This wrapper is scheduled. It enforces the time window and handles exit requests.
    """
    # If the runner was externally requested to stop, skip running.
    if _stop_event.is_set():
        return

    # If currently within the desired time window, run the task
    if within_window():
        logging.debug("Within time window, running task.")
        should_exit = main_task()
        if should_exit:
            logging.info("main_task requested exit. Stopping scheduler.")
            stop_runner()
    else:
        # If outside the window and past the end hour, stop the runner.
        # This causes the script to exit at or after END_HOUR automatically.
        current = now_time()
        end_time = datetime.time(hour=END_HOUR, minute=0, second=0)
        if current >= end_time:
            logging.info(
                "Current time is %s which is >= end time %s: stopping runner.",
                current.strftime("%H:%M:%S"),
                end_time.strftime("%H:%M:%S"),
            )
            stop_runner()
        else:
            logging.debug("Before start window: not running task yet.")


def stop_runner():
    """Signal to stop the scheduling loop and clear scheduled jobs."""
    _stop_event.set()
    schedule.clear()  # remove scheduled job entries
    logging.info("Scheduler cleared; runner will exit soon.")


def _signal_handler(signum, frame):
    logging.info("Received signal %s. Stopping runner...", signum)
    stop_runner()


def run_scheduler(interval_seconds=INTERVAL_SECONDS):
    """
    Set up schedule and run the loop until stop is requested.
    Uses a small sleep to remain responsive.
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Schedule the wrapper at the requested interval
    # We schedule every N seconds by using every().seconds.do
    schedule.every(interval_seconds).seconds.do(job_wrapper)

    logging.info(
        "Runner started: will execute between %02d:00 and %02d:00, every %s seconds.",
        START_HOUR,
        END_HOUR,
        interval_seconds,
    )

    # Run until stop event is set
    try:
        while not _stop_event.is_set():
            schedule.run_pending()
            # Sleep briefly so we don't busy-wait; keep resolution smaller than INTERVAL_SECONDS
            time.sleep(min(1, interval_seconds))
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt caught; stopping.")
        stop_runner()

    logging.info("Runner exiting.")
    # Optional: exit the process with status 0
    sys.exit(0)


if __name__ == "__main__":
    run_scheduler()