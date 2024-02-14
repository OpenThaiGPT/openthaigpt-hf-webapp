class ClientException(Exception):
    """User Exception are expected errors handled by the system
    when a user incorrectly performs an illegal operation

    This exception keeps a short message for the client to reac
    as well as a full error message as a traditional exception.
    """

    def __init__(self, client_msg: str, message: str):
        super().__init__(message)
        self.client_msg = client_msg
