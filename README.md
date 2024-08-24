Nothing to see here

Example transaction stored in db:

```
{
    _id: '100a0bfc2262898764382390aa8ca447',
    user: 'test',
    bank: 'test',
    account: {
        update_timestamp: '2024-08-24T09:31:47.526397Z',
        account_id: '56c7b029e0f8ec5a2334fb0ffc2fface',
        account_type: 'TRANSACTION',
        display_name: 'TRANSACTION ACCOUNT 1',
        currency: 'GBP',
        account_number: {
            iban: 'GB08CLRB04066800003435',
            swift_bic: 'CPBKGB00',
            number: '10000000',
            sort_code: '01-21-31'
        },
        provider: {
            display_name: 'MOCK',
            provider_id: 'mock',
            logo_uri: 'https://truelayer-client-logos.s3-eu-west-1.amazonaws.com/banks/banks-icons/mock-icon.svg'
        }
    },
    transaction: {
        timestamp: '2024-08-23T00:00:00Z',
        description: 'MORSES CLUB LTD',
        transaction_type: 'DEBIT',
        transaction_category: 'PURCHASE',
        transaction_classification: [
            'Personal Services',
            'Financial Services'
        ],
        merchant_name: 'Morses Club',
        amount: -30,
        currency: 'GBP',
        transaction_id: '100a0bfc2262898764382390aa8ca447',
        provider_transaction_id: '16736a7d4743f9aa69',
        normalised_provider_transaction_id: 'txn-b6894e0f055a9f52c',
        running_balance: {
            currency: 'GBP',
            amount: -626.02
        },
        meta: {
            provider_transaction_category: 'DEB'
        }
    }
}
```