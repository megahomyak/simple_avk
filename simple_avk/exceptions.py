LONGPOLL_ERROR_MSG = "Error in longpoll with code {}: {}"
VK_METHOD_ERROR_MSG = "Error in method {} with code {}: {}"


class MethodError(Exception):

    """
    Exception.
    Raised when an error is received from the VK method response.
    """

    def __init__(self, method_name: str, error_code: int, message: str) -> None:
        self.method_name = method_name
        self.error_code = error_code
        self.message = message

    def __str__(self) -> str:
        return VK_METHOD_ERROR_MSG.format(
            self.method_name,
            self.error_code,
            self.message
        )


class LongpollError(Exception):

    """
    Exception.
    Raised when an error is received from the VK longpoll.
    """

    def __init__(self, error_code: int, message: str) -> None:
        self.error_code = error_code
        self.message = message

    def __str__(self) -> str:
        return LONGPOLL_ERROR_MSG.format(
            self.error_code,
            self.message
        )
