from bunnet import init_bunnet
from pymongo import MongoClient

from transactions.odm.transaction import Transaction
from transactions.odm.bank_connection import BankConnection

import os

MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME")

if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME environment variables must be set")

client = MongoClient(MONGO_URI)


init_bunnet(client[MONGO_DB_NAME], document_models=[Transaction, BankConnection])

