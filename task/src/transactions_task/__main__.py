from transactions_task import task
from time import sleep

RUN_EVERY = 60 * 5

if __name__ == "__main__":
    while True:
        task()
        sleep(RUN_EVERY)