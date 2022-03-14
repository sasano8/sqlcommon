import sys
from typing import Any, NamedTuple

from lark import Lark, Transformer, v_args

json_grammar = r"""
    ?start: value

    ?value: object
          | array
          | kv
          | string
          | SIGNED_NUMBER      -> number
          | "true"             -> true
          | "false"            -> false
          | "null"             -> null

    array  : "[" [value ("," value)*] "]"
    object : "{" [pair ("," pair)*] "}"
    kv : "<" pair ">"
    pair   : string ":" value

    string : ESCAPED_STRING

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS

    %ignore WS
"""


class KeyValue(NamedTuple):
    key: str
    value: Any

    def __str__(self):
        return f"({self.key}, {self.value})"

    def __repr__(self):
        return f"('{self.key}', {self.value})"


class TreeToJson(Transformer):
    @v_args(inline=True)
    def string(self, s):
        return s[1:-1].replace('\\"', '"')

    def kv(self, s):
        return KeyValue(s[0][0], s[0][1])

    array = list
    pair = tuple
    object = dict
    number = v_args(inline=True)(float)

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False


### Create the JSON parser with Lark, using the LALR algorithm
json_parser = Lark(json_grammar, start="value")


def parse(text='("key": "value")'):
    tree = json_parser.parse(text)
    return TreeToJson().transform(tree)
