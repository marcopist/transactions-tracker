import schedule
import os
import time

from transactions.nordigen.lib import task
from loguru import logger

SCHEDULE_HOURS = os.environ.get("SCHEDULE_HOURS", "00 10 12 19").split(" ")

if __name__ == "__main__":
    for hour in SCHEDULE_HOURS:
        schedule.every().day.at(hour + ":00").do(task)
    while True:
        logger.info("Running scheduled tasks")
        schedule.run_pending()
        time.sleep(60)