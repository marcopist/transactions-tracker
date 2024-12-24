use chrono::prelude::*;
use iso_currency::Currency;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[pyclass]
struct CurrencyConversion {
    from_currency: Currency,
    to_currency: Currency,
    rate: f64,
}

#[derive(Debug, Serialize, Deserialize)]
#[pyclass]
pub struct TransactionAmount {
    pub amount: f64,
    pub currency: Currency,
}

#[derive(Debug, Serialize, Deserialize)]
#[pyclass]
pub enum TransactionType {
    OneOff,
    Periodic {
        from_date: DateTime<Utc>,
        to_date: DateTime<Utc>,
    },
}

#[derive(Debug, Serialize, Deserialize)]
#[pyclass]
struct TransactionTags {
    transaction_type: Option<TransactionType>,
}

#[derive(Debug, Serialize, Deserialize)]
#[pyclass]
pub struct Transaction {
    pub id: String,
    pub bank: String,
    pub account_id: String,
    pub transaction_datetime: DateTime<Utc>,
    pub transaction_amount: TransactionAmount,
    pub currency_conversion: Option<CurrencyConversion>,
    pub short_name: String,
    pub tags: TransactionTags,
}

#[pymethods]
impl Transaction {
    #[new]
    fn new(
        id: String,
        bank: String,
        account_id: String,
        transaction_datetime: DateTime<Utc>,
        transaction_amount: TransactionAmount,
        currency_conversion: Option<CurrencyConversion>,
        short_name: String,
        tags: TransactionTags,
    ) -> Self {
        Transaction {
            id,
            bank,
            account_id,
            transaction_datetime,
            transaction_amount,
            currency_conversion,
            short_name,
            tags,
        }
    }

    #[classmethod]
    fn from_dict(_cls: &PyType, dict: &PyDict) -> PyResult<Transaction> {
        let id = dict.get_item("id").unwrap().extract::<String>()?;
        let bank = dict.get_item("bank").unwrap().extract::<String>()?;
        let account_id = dict.get_item("account_id").unwrap().extract::<String>()?;
        let transaction_datetime = dict
            .get_item("transaction_datetime")
            .unwrap()
            .extract::<DateTime<Utc>>()?;
        let transaction_amount = dict
            .get_item("transaction_amount")
            .unwrap()
            .extract::<TransactionAmount>()?;
        let currency_conversion = dict
            .get_item("currency_conversion")
            .unwrap()
            .extract::<Option<CurrencyConversion>>()?;
        let short_name = dict.get_item("short_name").unwrap().extract::<String>()?;
        let tags = dict
            .get_item("tags")
            .unwrap()
            .extract::<TransactionTags>()?;

        Ok(Transaction {
            id,
            bank,
            account_id,
            transaction_datetime,
            transaction_amount,
            currency_conversion,
            short_name,
            tags,
        })
    }

    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("id", self.id.clone())?;
        dict.set_item("bank", self.bank.clone())?;
        dict.set_item("account_id", self.account_id.clone())?;
        dict.set_item("transaction_datetime", self.transaction_datetime.clone())?;
        dict.set_item("transaction_amount", self.transaction_amount.clone())?;
        dict.set_item("currency_conversion", self.currency_conversion.clone())?;
        dict.set_item("short_name", self.short_name.clone())?;
        dict.set_item("tags", self.tags.clone())?;
        Ok(dict.into())
    }

    #[classmethod]
    fn from_nordigen(_cls: &PyType, nordigen_data: &PyDict) -> Self {
        // transaction_amount = Amount(
        //     currency=nordigen_data["transactionAmount"]["currency"],
        //     amount=nordigen_data["transactionAmount"]["amount"],
        // )

        // transaction_type = UnknownTransaction()

        // short_name_waterfall = [
        //     nordigen_data.get("creditorName"),
        //     nordigen_data.get("debtorName"),
        //     nordigen_data.get("remittanceInformationUnstructured"),
        //     nordigen_data.get("additionalInformation"),
        // ]

        // short_name = next(
        //     (name for name in short_name_waterfall if name), None)

        // transaction_id = nordigen_data.get("transactionId")

        // if "currencyExchange" in nordigen_data:
        //     currency_exchange = nordigen_data["currencyExchange"]
        //     currency_conversion = CurrencyConversion(
        //         from_currency=currency_exchange["sourceCurrency"],
        //         to_currency=transaction_amount.currency,
        //         rate=currency_exchange["exchangeRate"],
        //     )
        // else:
        //     currency_conversion = None

        // transaction_datetime = next(
        //     (
        //         datetime.fromisoformat(nordigen_data.get(key))
        //         for key in ["valueDateTime", "bookingDateTime", "valueDate", "bookingDate"]
        //         if nordigen_data.get(key)
        //     ),
        //     None,
        // )

        // return cls(
        //     id=transaction_id,
        //     bank=bank,
        //     account_id=account_id,
        //     entry_reference=nordigen_data.get("entryReference"),
        //     transaction_datetime=transaction_datetime,
        //     transaction_amount=transaction_amount,
        //     currency_conversion=currency_conversion,
        //     short_name=short_name,
        //     transaction_type=transaction_type,
        // )

        let transaction_amount = nordigen_data
            .get_item("transactionAmount")
            .unwrap()
            .extract::<TransactionAmount>()
            .unwrap();
        let shortname_waterfall = vec![
            nordigen_data.get_item("creditorName"),
            nordigen_data.get_item("debtorName"),
            nordigen_data.get_item("remittanceInformationUnstructured"),
            nordigen_data.get_item("additionalInformation"),
        ];

        let short_name = shortname_waterfall
            .iter()
            .find(|name| name.is_some())
            .unwrap()
            .unwrap()
            .extract::<String>()
            .unwrap();

        let transaction_id = nordigen_data.get_item("transactionId").unwrap().extract::<String>().unwrap();

        let currency_conversion = if nordigen_data.contains("currencyExchange") {
            let currency_exchange = nordigen_data.get_item("currencyExchange").unwrap();
            let from_currency = currency_exchange.get_item("sourceCurrency").unwrap().extract::<Currency>().unwrap();
            let to_currency = transaction_amount.currency;
            let rate = currency_exchange.get_item("exchangeRate").unwrap().extract::<f64>().unwrap();
            Some(CurrencyConversion {
                from_currency,
                to_currency,
                rate,
            })
        } else {
            None
        };

        let transaction_datetime = vec![
            "valueDateTime",
            "bookingDateTime",
            "valueDate",
            "bookingDate",
        ]
    }
}

#[pymodule]
mod model_rs {
    use super::*;
}
