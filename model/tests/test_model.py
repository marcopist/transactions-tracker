from transactions_model import Transaction, Amount, OneOffTransaction
from datetime import datetime


def test_transaction_dump():
    transaction_date = datetime(2024, 1, 1)

    transaction = Transaction(
        _id="123",
        entry_reference="123",
        booking_date=transaction_date,
        value_date=transaction_date,
        transaction_amount=Amount(currency="USD", amount=100),
        transaction_type=OneOffTransaction(),
    )
    assert transaction.model_dump(mode="json", by_alias=True) == {
        "entryReference": "123",
        "bookingDate": transaction_date.isoformat(),
        "valueDate": transaction_date.isoformat(),
        "transactionAmount": {"currency": "USD", "amount": 100},
        "transactionType": {},
    }


def test_transaction_from_nordigen():
    transaction_json = {
        "transactionId": "yyy",
        "bookingDate": "2024-11-30",
        "bookingDateTime": "2024-11-30T03:23:22.152Z",
        "transactionAmount": {"amount": "-7.0000", "currency": "GBP"},
        "remittanceInformationUnstructured": "Perks",
        "proprietaryBankTransactionCode": "monzo_paid",
        "internalTransactionId": "zzz",
    }

    transaction = Transaction.from_nordigen(transaction_json)
    assert transaction.id == "tx_0000AoYViEmb6cycRoMRGb"


def test_transaction_from_nordigen2():
    transaction_json = {
        "transactionId": "xx",
        "entryReference": "xx",
        "bookingDate": "2024-12-01",
        "bookingDateTime": "2024-12-01T03:30Z",
        "transactionAmount": {"amount": "-5.4", "currency": "GBP"},
        "currencyExchange": {"sourceCurrency": "GBP", "exchangeRate": "1.0"},
        "creditorName": "TFL TRAVEL CHARGE",
        "remittanceInformationUnstructured": "TFL TRAVEL CHARGE",
        "additionalInformation": "xx",
        "merchantCategoryCode": "102",
    }

    transaction = Transaction.from_nordigen(transaction_json)
    assert transaction.transaction_amount.amount == -5.4


def test_transaction_from_nordigen3():
    transaction_json = {
        "transactionId": "zzz",
        "bookingDate": "2024-11-29",
        "bookingDateTime": "2024-11-29T14:10:21.28Z",
        "transactionAmount": {"amount": "15.0000", "currency": "GBP"},
        "debtorName": "Alice",
        "debtorAccount": {"bban": "xxx"},
        "remittanceInformationUnstructured": "Esempio",
        "proprietaryBankTransactionCode": "payport_faster_payments",
        "internalTransactionId": "zzz",
    }

    transaction = Transaction.from_nordigen(transaction_json)
    assert transaction.short_name == "Alice"


def test_transaction_round_trip():
    nordigen_json = {
        "transactionId": "zzz",
        "bookingDate": "2024-11-29",
        "bookingDateTime": "2024-11-29T14:10:21.28Z",
        "transactionAmount": {"amount": "15.0000", "currency": "GBP"},
        "debtorName": "Alice",
        "debtorAccount": {"bban": "xxx"},
        "remittanceInformationUnstructured": "Esempio",
        "proprietaryBankTransactionCode": "payport_faster_payments",
        "internalTransactionId": "zzz",
    }

    transaction = Transaction.from_nordigen(nordigen_json)

    transaction_json = transaction.to_json()

    expected_result = {
        "_id": "zzz",
        "entryReference": None,
        "bookingDate": "2024-11-29T14:10:21.280000Z",
        "valueDate": None,
        "transactionAmount": {"currency": "GBP", "amount": 15.0},
        "currencyConversion": None,
        "shortName": "Alice",
        "transactionType": {"transactionType": "unknown"},
    }

    assert transaction_json == expected_result

    transaction2 = Transaction.from_json(transaction_json)

    assert transaction == transaction2
