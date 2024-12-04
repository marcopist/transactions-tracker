from transactions_task import task
from loguru import logger

if __name__ == "__main__":
    logger.info("Starting task script")
    task()
    logger.info("Task script finished")
