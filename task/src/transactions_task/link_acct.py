from transactions_task import link_account

if __name__ == "__main__":
    acct_to_link = input("Enter the account to link: ")
    link = link_account(acct_to_link)
    print(link)
