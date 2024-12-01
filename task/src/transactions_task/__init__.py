import os, sys

import uuid
from nordigen import NordigenClient
from requests import HTTPError
from pymongo import MongoClient
from loguru import logger


GO_CARDLESS_SECRET_ID = os.getenv("GO_CARDLESS_SECRET_ID")
GO_CARDLESS_SECRET_KEY = os.getenv("GO_CARDLESS_SECRET_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if MONGO_URI is None:
    raise ValueError("MONGO_URI is not set")

nordigen_client = NordigenClient(GO_CARDLESS_SECRET_KEY, GO_CARDLESS_SECRET_ID)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["transactions"]
sessions_collection = db["sessions"]
transactions_collection = db["transactions"]


token_data = nordigen_client.generate_token()


def retry_with_new_token(func):
    global token_data

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            error_code = e["status_code"]
            if error_code == 401:
                token_data = nordigen_client.exchange_token(token_data["refresh"])
                nordigen_client.token = token_data["access"]
                return func(*args, **kwargs)
            raise e

    return wrapper


@retry_with_new_token
def link_account(bank_name: str):
    if bank_name == "sandbox":
        institution = "SANDBOXFINANCE_SFIN0000"
    else:
        institution = nordigen_client.institution.get_institution_id_by_name(
            country="GB",
            institution=bank_name,
        )
    session = nordigen_client.initialize_session(
        institution_id=institution,
        redirect_uri="http://localhost:3000",
        reference_id=str(uuid.uuid4())
    )
    requisition_id = session.requisition_id
    sessions_collection.insert_one({"requisition_id": requisition_id})
    return session.link


@retry_with_new_token
def get_all_transactions():
    sessions = sessions_collection.find()

    transactions = []
    for session in sessions:
        requisition_id = session["requisition_id"]
        requisition = nordigen_client.requisition.get_requisition_by_id(requisition_id)
        if requisition["status"] != "LN":
            logger.info(f"Requisition {requisition_id} is not working")

        accounts = requisition["accounts"]

        for account_id in accounts:
            account = nordigen_client.account_api(id=account_id)
            acct_transactions = account.get_transactions()["transactions"]
            all_transactions = acct_transactions["booked"] + acct_transactions["pending"]
            transactions.extend(all_transactions)

    return transactions


def add_id_to_transaction(transaction):
    transaction["_id"] = transaction["transactionId"]
    return transaction


@retry_with_new_token
def task():
    online_transactions = get_all_transactions()

    logger.info(f"Got {len(online_transactions)} transactions")

    transactions_already_present = [
        transaction["_id"]
        for transaction in transactions_collection.find(
            {
                "_id": {
                    "$in": [
                        transaction["transactionId"]
                        for transaction in online_transactions
                    ]
                }
            }
        )
    ]

    logger.info(f"{len(transactions_already_present)} were already present")

    transactions_to_insert = [
        add_id_to_transaction(transaction)
        for transaction in online_transactions
        if transaction["transactionId"] not in transactions_already_present
    ]

    logger.info(f"Loading {len(transactions_to_insert)} transactions into Mongodb")

    transactions_collection.insert_many(transactions_to_insert)
