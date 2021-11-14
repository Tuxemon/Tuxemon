#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
#

from __future__ import annotations
from tuxemon.item.itemcondition import ItemCondition
from typing import NamedTuple, Any, Mapping, Callable
from tuxemon.script_context import ScriptContext
import re
import ast
import operator
import itertools

# For now, the expression must be "<value> <op> <value>"
# If the need arises more complex things can be implemented in the
# future using regular expressions or grammar parsers.
quoted_string_regex = r'(?:"(?:\\.|[^"\\])*")'
number_regex = r'(?:(?:\+|-)?[0-9]+\.?[0-9]*)'
variable_regex = r'(?:\w+(?:\.\w+)*)'
operator_regex = r'(?:(?:==)|(?:!=)|(?:>=)|(?:<=)|>|<|(?:and)|(?:or)|(?:in)|&|\|)'
primitive_value_regex = fr'(?:{quoted_string_regex}|{number_regex}|{variable_regex}|(?:True)|(?:False)|(?:None))'
set_regex = fr'(?:{{\s*{primitive_value_regex}(?:\s*,\s*{primitive_value_regex}\s*)*\s*}})'
capture_set_regex = fr'{{\s*({primitive_value_regex})((?:\s*,\s*{primitive_value_regex}\s*)*)\s*}}'
capture_set_last_element_regex = fr'\s*,\s*({primitive_value_regex})\s*'
value_regex = fr'(?:{primitive_value_regex}|{set_regex})'
full_regex = fr'({value_regex})\s*({operator_regex})\s*({value_regex})'
compiled_capture_set_regex = re.compile(capture_set_regex)
compiled_capture_set_last_element_regex = re.compile(
    capture_set_last_element_regex,
)
compiled_regex = re.compile(full_regex)


operator_dict: Mapping[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "and": lambda a, b: bool(a) and bool(b),
    "or": lambda a, b: bool(a) or bool(b),
    "in": lambda a, b: a in b,
    "&": operator.and_,
    "|": operator.or_,
}


class EvalConditionParameters(NamedTuple):
    expression: str


class EvalCondition(ItemCondition[EvalConditionParameters]):
    """Evaluate a expression."""

    name = "eval"
    param_class = EvalConditionParameters

    def _parse_primitive_value(
        self, value: str,
        context: ScriptContext,
    ) -> Any:

        try:
            return ast.literal_eval(value)
        except ValueError:
            return context.get_variable(value)

    def _parse_value(self, value: str, context: ScriptContext) -> Any:

        result = compiled_capture_set_regex.fullmatch(
            value,
        )
        if result:
            # Parse a set

            first, rest = result.groups()

            return {
                self._parse_primitive_value(v, context)
                for v in itertools.chain(
                    (first,),
                    (
                        x.group(1) for x
                        in compiled_capture_set_last_element_regex.finditer(
                            rest,
                        )
                    ),
                )
            }

        else:
            # Parse a primitive value
            return self._parse_primitive_value(value, context)

    def test(self, context: ScriptContext) -> bool:

        result = compiled_regex.fullmatch(self.parameters.expression)
        if result:
            value1, operator, value2 = result.groups()

            value1 = self._parse_value(value1, context)
            value2 = self._parse_value(value2, context)

            return bool(operator_dict[operator](value1, value2))

        else:
            raise ValueError(
                f"Bad expression syntax: "
                f"'{self.parameters.expression}' does not match '{full_regex}'"
            )
