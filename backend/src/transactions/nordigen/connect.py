from transactions.nordigen.lib import link_account

if __name__ == "__main__":
    print("Enter the bank name to link the account")
    bank_name = input()
    url = link_account(bank_name)
    print(f"Click on the link to link the account: {url}")