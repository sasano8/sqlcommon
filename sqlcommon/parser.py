import os

from lark import Lark, Transformer, v_args

path = os.path.dirname(__file__)


class SqlTransformer(Transformer):
    bool = bool
    number = v_args(inline=True)(float)
    string = str
    true = lambda self, _: True
    false = lambda self, _: False
    STAR = str

    @v_args(inline=True)
    def name(self, s):
        if s[0] == '"' and s[len(s) - 1] == '"':
            s = s[1 : len(s) - 2]
        return s
        # return s.replace("''", "'")

    @v_args(inline=True)
    def alias_string(self, s):
        return self.name(s)

    def table(self, tree):
        return {
            "type": "table",
            "name": tree[1],
            "schema": tree[0],
            "alias": tree[2],
        }

    def column_name(self, tree):
        return {
            "type": "col",
            "name": tree[1],
            "table": tree[0],
        }

    def select_expression(self, tree):
        col = tree[0]
        alias = tree[1]
        return {**col, "alias": alias}

    def returning_expression(self, tree):
        return ("RETURNING", list(tree))

    def from_expression(self, tree):
        return ("FROM", list(tree))

    def where_expression(self, tree):
        return ("WHERE", list(tree))

    def having_expression(self, tree):
        return ("HAVING", list(tree))

    def group_by_expression(self, tree):
        return ("GROUP_BY", list(tree))

    def order_by_expression(self, tree):
        return ("ORDER_BY", list(tree))

    def join_expression(self, tree):
        return ("JOIN", list(tree))

    def cross_join_expression(self, tree):
        return ("CROSS_JOIN", list(tree))

    def select(self, tree):
        return ("SELECT", list(tree))

    def union_distinct(self, tree):
        return ("UNION", list(tree))

    def union_all(self, tree):
        return ("UNION_ALL", list(tree))

    def intersect_distinct(self, tree):
        return ("INTERSECT", list(tree))

    def except_distinct(self, tree):
        return ("EXCEPT", list(tree))

    def except_all(self, tree):
        return ("EXCEPT_ALL", list(tree))


def parse(text: str):
    with open(path + "/grammer.lark") as grammer:
        parser = Lark(grammer.read(), start="start")
        tree = parser.parse(text)
        result = SqlTransformer().transform(tree)
        return result


def new_parse(text: str):
    with open(path + "/grammer2.lark") as grammer:
        parser = Lark(grammer.read(), start="start")
        tree = parser.parse(text)
        result = SqlTransformer().transform(tree)
        return result
