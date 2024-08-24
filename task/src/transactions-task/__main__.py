import logging
import os
import sys
import time
import urllib.parse
import os

from functools import reduce

import requests
from pymongo import MongoClient

TRUELAYER_ENVIRONMENT = os.environ.get("TRUELAYER_ENVIRONMENT", "sandbox")
TRUELAYER_CLIENT_ID = os.environ.get("TRUELAYER_CLIENT_ID")
TRUELAYER_CLIENT_SECRET = os.environ.get("TRUELAYER_CLIENT_SECRET")
TRUELAYER_DOMAIN = {
    "sandbox": "truelayer-sandbox.com",
    "production": "truelayer.com",
}[TRUELAYER_ENVIRONMENT]

MONGO_URI = "db"



mongo_client = MongoClient(host=MONGO_URI)
transactions = mongo_client["transactions"]["transactions"]
users = mongo_client["transactions"]["users"]

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler("/tmp/transactions-task.log"))

class ExpiredTokenError(Exception):
    def __init__(self, user, bank):
        self.user = user
        self.bank = bank
        super().__init__(f"Refresh token failed for user {user['_id']} and bank {bank}")

def sync_transactions():
    while True:
        logger.info(f"Syncing transactions for {users.count_documents({})} users")
        for user in users.find():
            logger.info(f"Syncing transactions for user {user['_id']}")
            process_user(user)
        time.sleep(60)

def process_user(user):
    try:
        refresh_bank_accounts(user)
        sync_user_transactions(user)
    except ExpiredTokenError as e:
        logger.info(f"Refreshing token for user {e.user['_id']} and bank {e.bank}")
        user = refresh_token(e.user, e.bank)
        process_user(user)


def sync_user_transactions(user):
    transactions = get_all_user_transactions(user)
    for transaction in transactions:
        update_transaction(transaction)
    logger.info(f"Synced transactions for user {user['_id']}")

9
def format_transaction(user, bank, account, transaction):
    user_id = user["_id"]
    return {
        "_id": transaction["transaction_id"],
        "user": user_id,
        "bank": bank,
        "account": account,
        "transaction": transaction,
    }


def refresh_bank_accounts(user):
    for bank in user["banks"]:
        accounts = get_accounts(user, bank)["results"]
        user["banks"][bank]["accounts"] = accounts
    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"banks": user["banks"]}},
    )


def get_all_user_transactions(user):
    """Get all transactions for a user across all banks and accounts.
    Transactions are formatted in the following way:
    {
        "_id": "transaction_id",
        "user": "user_id",
        "bank": "bank_id",
        "account": "account_id",
        "transaction": {
            "transaction_id": "transaction_id",
            "timestamp": "timestamp",
            "description": "description",
            "amount": "amount",
            "currency": "currency",
            "meta": "meta",
        }
    }
    """
    transactions = []
    for bank in user["banks"]:
        for account in user["banks"][bank].get("accounts", []):
            account_transactions = get_transactions(
                user,
                bank,
                account
            )["results"]
            transactions.extend(
                map(
                    lambda transaction: format_transaction(user, bank, account, transaction),
                    account_transactions,
                )
            )
    return transactions


def get_accounts(user, bank):
    access_token = user["banks"][bank]["access_token"]
    url = f"https://api.{TRUELAYER_DOMAIN}/data/v1/accounts"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        raise ExpiredTokenError(user, bank)

    return response.json()


def get_transactions(user, bank, account):
    token = user["banks"][bank]["access_token"]
    account_id = account["account_id"]
    url = f"https://api.{TRUELAYER_DOMAIN}/data/v1/accounts/{account_id}/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise ExpiredTokenError(user, bank)
    return response.json()


def build_url(base_url, path, args_dict):
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)


def update_transaction(transaction):
    loaded = transactions.find_one({"_id": transaction["_id"]})
    if loaded:
        if loaded["transaction"] != transaction["transaction"]:
            transactions.update_one({"_id": transaction["_id"]}, {"$set": transaction})
            logger.info(f"Updated transaction {transaction['_id']}")
        else:
            logger.debug(f"Transaction {transaction['_id']} already up to date")
    else:
        transactions.insert_one(transaction)
        logger.info(f"Inserted transaction {transaction['_id']}")


def refresh_token(user, bank):
    refresh_token = user["banks"][bank]["refresh_token"]
    url = f"https://auth.{TRUELAYER_DOMAIN}/connect/token"
    payload = {
        "client_id": TRUELAYER_CLIENT_ID,
        "client_secret": TRUELAYER_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=payload).json()
    access_token = response["access_token"]
    refresh_token = response["refresh_token"]
    user["banks"][bank]["access_token"] = access_token
    user["banks"][bank]["refresh_token"] = refresh_token
    users.update_one({"_id": user["_id"]}, {"$set": user})
    return user


if __name__ == "__main__":
    sync_transactions()
