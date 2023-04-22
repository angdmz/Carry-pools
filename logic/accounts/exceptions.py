from exceptions import ResourceNotFound


class AccountNotFound(ResourceNotFound):
    def __init__(self, address):
        super().__init__(f"Address not found: {address}")


class AccountControllerNotFound(ResourceNotFound):
    def __init__(self, address, participant_id):
        super().__init__(f"No controller found: address {address} - participant ID: {participant_id}")
