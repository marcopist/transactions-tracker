import os

import uuid
from nordigen import NordigenClient
from requests import HTTPError
from loguru import logger
from transactions.odm import Transaction, BankConnection

GO_CARDLESS_SECRET_ID = os.getenv("GO_CARDLESS_SECRET_ID")
GO_CARDLESS_SECRET_KEY = os.getenv("GO_CARDLESS_SECRET_KEY")

nordigen_client = NordigenClient(GO_CARDLESS_SECRET_KEY, GO_CARDLESS_SECRET_ID)

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
    BankConnection.new(id=requisition_id, bank_name=bank_name)
    return session.link


@retry_with_new_token
def task():
    bank_connections = list(BankConnection.find())
    logger.info(f"Found {len(bank_connections)} bank connections")
    for bank_connection in bank_connections:
        bank_name = bank_connection.bank_name
        logger.info(f"Processing transactions for bank connection {bank_name}")
        requisition_id = bank_connection.id
        requisition = nordigen_client.requisition.get_requisition_by_id(requisition_id)
        if requisition["status"] != "LN":
            logger.error(f"Connection with {bank_name} is not working")
            continue

        accounts = requisition["accounts"]

        for account_id in accounts:
            account = nordigen_client.account_api(id=account_id)
            acct_transactions = account.get_transactions()["transactions"]
            num_pending_transactions = len(acct_transactions.get("pending", []))
            num_booked_transactions = len(acct_transactions.get("booked", []))
            logger.info(
                f"Found {num_pending_transactions} pending transactions and {num_booked_transactions} booked transactions for account {account_id} at {bank_name}"
            )
            Transaction.process_nordigen_data(acct_transactions, bank_name)
            logger.info(f"Processed transactions for account {account_id} at {bank_name}")

        logger.info(f"Processed transactions for all accounts at {bank_name}")

    logger.info("Processed transactions for all bank connections")
