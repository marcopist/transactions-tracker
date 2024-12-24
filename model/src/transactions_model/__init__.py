from typing import Optional
from typing_extensions import Literal
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from pydantic.alias_generators import to_camel
from iso4217 import Currency

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Amount(BaseSchema):
    currency: Currency
    amount: float


class CurrencyConversion(BaseSchema):
    from_currency: Currency
    to_currency: Currency
    rate: float


class PeriodicTransaction(BaseSchema):
    transaction_type: Literal["periodic"] = "periodic"
    from_date: datetime
    to_date: datetime


class OneOffTransaction(BaseSchema):
    transaction_type: Literal["one_off"] = "one_off"


class UnknownTransaction(BaseSchema):
    transaction_type: Literal["unknown"] = "unknown"


TransactionType = PeriodicTransaction | OneOffTransaction | UnknownTransaction


class Transaction(BaseSchema):
    id: str = Field(alias="_id")
    bank: str
    account_id: str
    entry_reference: Optional[str]
    transaction_datetime: datetime
    transaction_amount: Amount
    currency_conversion: Optional[CurrencyConversion]
    short_name: str
    transaction_type: TransactionType = Field(discriminator="transaction_type")

    def to_json(self):
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, json_data: dict):
        return cls.model_validate(json_data)

    @classmethod
    def from_nordigen(cls, nordigen_data: dict, bank: str, account_id: str):
        transaction_amount = Amount(
            currency=nordigen_data["transactionAmount"]["currency"],
            amount=nordigen_data["transactionAmount"]["amount"],
        )

        transaction_type = UnknownTransaction()

        short_name_waterfall = [
            nordigen_data.get("creditorName"),
            nordigen_data.get("debtorName"),
            nordigen_data.get("remittanceInformationUnstructured"),
            nordigen_data.get("additionalInformation"),
        ]

        short_name = next(
            (name for name in short_name_waterfall if name), None)

        transaction_id = nordigen_data.get("transactionId")

        if "currencyExchange" in nordigen_data:
            currency_exchange = nordigen_data["currencyExchange"]
            currency_conversion = CurrencyConversion(
                from_currency=currency_exchange["sourceCurrency"],
                to_currency=transaction_amount.currency,
                rate=currency_exchange["exchangeRate"],
            )
        else:
            currency_conversion = None

        transaction_datetime = next(
            (
                datetime.fromisoformat(nordigen_data.get(key))
                for key in ["valueDateTime", "bookingDateTime", "valueDate", "bookingDate"]
                if nordigen_data.get(key)
            ),
            None,
        )

        return cls(
            id=transaction_id,
            bank=bank,
            account_id=account_id,
            entry_reference=nordigen_data.get("entryReference"),
            transaction_datetime=transaction_datetime,
            transaction_amount=transaction_amount,
            currency_conversion=currency_conversion,
            short_name=short_name,
            transaction_type=transaction_type,
        )

    def process_nordigen_update(
        self,
        new_transaction: "Transaction",
    ):
        if self.id != new_transaction.id:
            raise ValueError("Transaction ids do not match")
        self.transaction_datetime = new_transaction.transaction_datetime
        self.transaction_amount = new_transaction.transaction_amount
        self.short_name = new_transaction.short_name
        return self
