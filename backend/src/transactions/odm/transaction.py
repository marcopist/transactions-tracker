from datetime import datetime
from enum import Enum
from functools import partial
from itertools import chain
from bunnet import Document, Indexed
from iso4217 import Currency
from pydantic import BaseModel
import dateutil.parser as date_parser


class Amount(BaseModel):
    currency: Currency
    amount: float


class Tag:
    __class__ = type("Tag", (BaseModel,), {})

    class OneOff(__class__):
        ...

    class Periodic(__class__):
        from_date: datetime
        to_date: datetime

    class Untagged(__class__):
        ...

    _members = [
        OneOff,
        Periodic,
        Untagged,
    ]


class TransactionStatus(Enum):
    BOOKED = "booked"
    PENDING = "pending"


class Transaction(Document):
    id: str
    bank: Indexed(str)
    datetime: Indexed(datetime)
    amount: Amount
    short_name: str
    status: TransactionStatus
    tags: None

    class Settings:
        name = "transactions"

    def apply_tag(self, tag: Tag):
        self.tags = tag
        self.save()

    @classmethod
    def from_nordigen(cls, data, bank, status):
        id_ = data["transactionId"]

        datetime_waterfall = [
            data.get("bookingDateTime"),
            data.get("valueDateTime"),
            data.get("bookingDate"),
            data.get("valueDate"),
        ]

        datetime_ = next(
            (date_parser.parse(d) for d in datetime_waterfall if d is not None), None
        )

        amount_ = data["transactionAmount"]["amount"]
        currency = data["transactionAmount"]["currency"]
        amount = Amount(currency=currency, amount=amount_)

        short_name_waterfall = [
            data.get("creditorName"),
            data.get("debtorName"),
            data.get("remittanceInformationUnstructured"),
        ]

        short_name = next(
            (name for name in short_name_waterfall if name is not None), None
        )

        return cls(
            id=id_,
            bank=bank,
            datetime=datetime_,
            amount=amount,
            short_name=short_name,
            status=status,
            tags=None,
        )

    @classmethod
    def process_nordigen_data(cls, nordigen_transactions, bank):
        nordigen_booked_transactions = nordigen_transactions.get("booked", [])
        nordgen_pending_transactions = nordigen_transactions.get("pending", [])

        booked_transactions = map(
            partial(cls.from_nordigen, bank=bank, status=TransactionStatus.BOOKED),
            nordigen_booked_transactions,
        )
        pending_transactions = map(
            partial(cls.from_nordigen, bank=bank, status=TransactionStatus.PENDING),
            nordgen_pending_transactions,
        )

        incoming_transactions = chain(booked_transactions, pending_transactions)

        for incoming_transaction in incoming_transactions:
            current_transaction = (
                cls.get(incoming_transaction.id).run() or incoming_transaction
            )
            current_transaction._update(incoming_transaction).save()

    def _update(self, other):
        self.amount = other.amount
        self.short_name = other.short_name
        self.datetime = other.datetime
        return self

    def tag(self, tag):
        self.tags = tag
        return self