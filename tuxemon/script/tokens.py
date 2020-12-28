__all__ = [
    "EventToken",
    "EventPropertyToken",
    "PriorityToken",
    "ActionNameToken",
    "ConditionNameToken",
    "OperatorToken",
    "ArgumentToken",
]


class Token:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.args}, {self.kwargs}>"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.args}, {self.kwargs}>"

    def __eq__(self, other):
        return type(self) == type(other) and self.args == other.args and self.kwargs == other.kwargs

    @property
    def value(self):
        return self.args[0]


class EventToken(Token):
    """Contains actions and conditions"""


class EventPropertyToken(Token):
    """Either an action or condition"""


class PriorityToken(Token):
    """Priority of action/condition (property)"""


class ActionNameToken(Token):
    """Name of action to execute"""


class ConditionNameToken(Token):
    """Name of condition to check"""


class OperatorToken(Token):
    """Operator for conditionals; either is or not"""


class ArgumentToken(Token):
    """A single argument for a action or condition"""
