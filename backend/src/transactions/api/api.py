from fastapi import FastAPI
from transactions.odm import Transaction

app = FastAPI()

@app.get("/transactions")
def get_transactions():
    return Transaction.find_all().run()