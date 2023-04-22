from fastapi import Depends

from settings import AccountsSettings


def get_accounts_settings():
    return AccountsSettings()

def get_balance_limit_per_account(settings: AccountsSettings = Depends(get_accounts_settings)):
    return settings.balance_limit
