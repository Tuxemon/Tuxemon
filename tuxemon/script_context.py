from __future__ import annotations
from typing import Optional, Any


class ScriptContext():

    def __init__(self, parent: Optional[ScriptContext] = None) -> None:
        self.parent = parent

    def get_variable(self, name: str) -> Any:

        variable_path = name.split(".")

        obj = self
        for a in variable_path:
            obj = getattr(obj, a)

        return obj

    def set_variable(self, name: str, value: Any) -> None:

        variable_path = name.split(".")

        obj = self
        for a in variable_path[:-1]:
            obj = getattr(obj, a)

        setattr(obj, variable_path[-1], value)
