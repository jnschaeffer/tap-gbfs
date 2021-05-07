class UnknownSystemError(Exception):
    def __init__(self, system_id):
        msg = f"unknown system {system_id}"
        super().__init__(msg)
