import logging
import os
import flask
import urllib.parse

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

app = flask.Flask(__name__)

LOGGER = logging.getLogger(__name__)

MONGO_CLIENT = MongoClient(host=MONGO_URI)
TRANSACTIONS = MONGO_CLIENT["transactions"]["transactions"]
USERS = MONGO_CLIENT["transactions"]["users"]

def build_url(base_url, path, args_dict):
    # Returns a list in the structure of urlparse.ParseResult
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)


@app.route("/link")
def make_truelayer_transaction_link():

    params = {
        "response_type": "code",
        "client_id": TRUELAYER_CLIENT_ID,
        "redirect_uri": "https://console.truelayer.com/redirect-page",
        "scope": "info accounts balance cards transactions direct_debits standing_orders offline_access",
    }

    if TRUELAYER_ENVIRONMENT == "sandbox":
        params["providers"] = "uk-cs-mock uk-ob-all uk-oauth-all"
    else:
        params["providers"] = "uk-ob-all uk-oauth-all"

    link = build_url(f"https://auth.{TRUELAYER_DOMAIN}/", "", params)

    return link


@app.route("/store/<user>/<bank>/<code>")
def exchange_code_for_token(user, bank, code):
    url = f"https://auth.{TRUELAYER_DOMAIN}/connect/token"
    payload = {
        "client_id": TRUELAYER_CLIENT_ID,
        "client_secret": TRUELAYER_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://console.truelayer.com/redirect-page",
    }
    response = requests.post(url, data=payload).json()
    access_token = response["access_token"]
    refresh_token = response["refresh_token"]
    USERS.update_one(
        {"_id": user},
        {
            "$set": {
                f"banks.{bank}.access_token": access_token,
                f"banks.{bank}.refresh_token": refresh_token,
            }
        },
        upsert=True,
    )

    return "Done"


if __name__ == "__main__":
    app.run(host="0.0.0.0:8000")
