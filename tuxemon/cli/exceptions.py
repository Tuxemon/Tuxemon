class CommandNotFoundError(Exception):
    """
    Raised when a command is not found.

    """


class ParseError(Exception):
    """
    Raised when the input cannot be parsed due to bad syntax.

    """
