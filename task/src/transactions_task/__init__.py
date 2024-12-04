import os

import uuid
from nordigen import NordigenClient
from requests import HTTPError
from pymongo import MongoClient
from loguru import logger
from transactions_model import Transaction

GO_CARDLESS_SECRET_ID = os.getenv("GO_CARDLESS_SECRET_ID")
GO_CARDLESS_SECRET_KEY = os.getenv("GO_CARDLESS_SECRET_KEY")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
MONGO_URI = os.getenv("MONGO_URI")

if MONGO_URI is None:
    raise ValueError("MONGO_URI is not set")

nordigen_client = NordigenClient(GO_CARDLESS_SECRET_KEY, GO_CARDLESS_SECRET_ID)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["transactions"]
sessions_collection = db["sessions"]
if not DRY_RUN:
    transactions_collection = db["transactions"]
else:
    transactions_collection = db["sandbox_transactions"]


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
        reference_id=str(uuid.uuid4()),
    )
    requisition_id = session.requisition_id
    sessions_collection.insert_one(
        {"requisition_id": requisition_id, "bank_name": bank_name}
    )
    return session.link


@retry_with_new_token
def get_all_transactions():
    if not DRY_RUN:
        sessions = sessions_collection.find({"$not": {"bank_name": "sandbox"}})
    else:
        sessions = sessions_collection.find({"bank_name": "sandbox"})

    transactions = []
    for session in sessions:
        bank_name = session["bank_name"]
        requisition_id = session["requisition_id"]
        requisition = nordigen_client.requisition.get_requisition_by_id(requisition_id)
        if requisition["status"] != "LN":
            logger.info(f"Requisition {requisition_id} is not working")

        accounts = requisition["accounts"]

        for account_id in accounts:
            account = nordigen_client.account_api(id=account_id)
            acct_transactions = account.get_transactions()["transactions"]
            all_transactions = (
                acct_transactions["booked"] + acct_transactions["pending"]
            )
            transactions.extend([Transaction.from_nordigen(t, bank_name, account_id) for t in all_transactions])

    return transactions


@retry_with_new_token
def task():
    online_transactions = list(get_all_transactions())

    logger.info(f"Got {len(online_transactions)} transactions")

    for transaction in online_transactions:
        loaded_transaction = transactions_collection.find_one(
            {"_id": transaction.id}
        )

        if loaded_transaction is None:
            transactions_collection.insert_one(transaction.to_json())
            logger.info(f"Inserted transaction {transaction.id}")
        else:
            updated_transaction = loaded_transaction.process_nordigen_update(transaction)
            transactions_collection.update_one(
                {"_id": transaction.id},
                {"$set": updated_transaction.to_json()},
            )
            logger.info(f"Transaction {transaction.id} already exists")
            