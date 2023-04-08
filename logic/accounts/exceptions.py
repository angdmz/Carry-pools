from exceptions import ResourceNotFound


class AccountNotFound(ResourceNotFound):
    def __init__(self, address):
        super().__init__(f"Address not found: {address}")
