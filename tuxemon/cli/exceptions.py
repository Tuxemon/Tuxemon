class CommandNotFoundError(Exception):
    """
    Raised when a command is not found

    """

    pass


class ParseError(Exception):
    """
    Raised when the input cannot be parsed due to bad syntax

    """

    pass
