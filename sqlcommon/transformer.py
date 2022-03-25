import os
from typing import Literal

from lark import Lark, Transformer, v_args

from .tokens import (
    BinaryOperator,
    Bracket,
    Column,
    Expressions,
    Func,
    Identifier,
    JoinStatement,
    Postfix,
    Prefix,
    SelectStatement,
    Table,
    UnionStatement,
    Value,
)

path = os.path.dirname(__file__)


def Node(name, arr):
    return (name, arr)


def Term(val):
    return ("TERM", val)


class CommonTransformer(Transformer):
    true = lambda self, _: True
    false = lambda self, _: False
    int = v_args(inline=True)(int)
    float = v_args(inline=True)(float)
    null = lambda self, _: None
    STAR = str
    BOPS = v_args(inline=True)(str)
    SIGN = v_args(inline=True)(str)

    def RESERVED_WORDS(self, tree):
        raise NotImplementedError(f"Invalid syntax: {str(tree)}")

    def STRING_LITERAL(self, s):
        return s[1:-1]

    def str(self, strings):
        return "".join(strings)

    @v_args(inline=True)
    def NAME(self, s):
        if s[0] == '"' and s[len(s) - 1] == '"':
            s = s[1 : len(s) - 2]
            return s
        else:
            return str(s)

    @v_args(inline=True)
    def alias_string(self, s):
        return self.NAME(s)

    def identifier(self, tree):
        schema_or_table, name = tree
        return Identifier(name=name, parent=schema_or_table)

    def func(self, tree):
        schema_or_table, name, *expr = tree
        return Func(name=name, parent=schema_or_table, args=Expressions(*expr))

    def item(self, tree):
        obj, alias = tree
        if isinstance(obj, dict):
            obj["is_item"] = True
            obj["alias"] = alias
        else:
            obj = Value(obj, alias=alias)
            obj["is_item"] = True

        return obj

    def ASC_OR_DESC(self, tree):
        return str(tree).upper()

    def sign_expr(self, tree):
        return Postfix(op=tree[0], expr=Expressions(tree[1]))

    def bo_expr(self, tree):
        return BinaryOperator(op=tree[1], expr=Expressions(tree[0], tree[2]))

    def expr(self, tree):
        return tree

    items = lambda self, tree: Expressions(*tree)
    order_items = lambda self, tree: Expressions(*tree)

    def order_item(self, tree):
        obj, asc_or_desc = tree
        if asc_or_desc == "ASC":
            is_asc = True
        elif asc_or_desc == "DESC":
            is_asc = False
        elif asc_or_desc is None:
            is_asc = None
        else:
            raise RuntimeError()

        obj["is_asc"] = is_asc
        return obj


class SelectTransformer(CommonTransformer):
    returning_stmt = lambda self, tree: Node("RETURNING", tree[0])
    from_stmt = lambda self, tree: Node("FROM", tree[0])
    orderby_stmt = lambda self, tree: Node("ORDERBY", tree[0])
    groupby_stmt = lambda self, tree: Node("GROUPBY", tree[0])
    where_stmt = lambda self, tree: Node("WHERE", tree[0])
    having_stmt = lambda self, tree: Node("HAVING", tree[0])
    window_stmt = lambda self, tree: Node("WINDOW", tree[0])
    limit_stmt = lambda self, tree: Node("LIMIT", tree[0])
    offset_stmt = lambda self, tree: Node("OFFSET", tree[0])

    query_stmt = lambda self, tree: Node("QUERY", Expressions(*tree))

    union_all_stmt = lambda self, tree: self._union_stmt("UNION", tree)
    intersect_stmt = lambda self, tree: self._union_stmt("INTERSECT", tree)
    except_stmt = lambda self, tree: self._union_stmt("EXCEPT", tree)

    def join_type(self, tree):
        return " ".join(tree).upper()

    def join_on_items(self, tree):
        return tree

    def join_using_items(self, tree):
        def create_identifier(name):
            obj = Identifier(name=name, parent=None)
            obj["is_item"] = True
            # obj["alias"] = None
            return obj

        return [create_identifier(x) for x in tree]

    def join_on_stmt(self, tree):
        return Node("ON", tree[0])

    def join_using_stmt(self, tree):
        return Node("USING", tree[0])

    def join_stmt(self, tree):
        join_type, items, on_or_using_stmt = tree
        if on_or_using_stmt[0] == "ON":
            return JoinStatement(join_type, from_=items, on=on_or_using_stmt[1])
        elif on_or_using_stmt[0] == "USING":
            return JoinStatement(join_type, from_=items, using=on_or_using_stmt[1])
        else:
            raise RuntimeError()

    def join_stmts(self, tree):
        return Node("JOIN", Expressions(*tree))

    def _union_stmt(self, union_name, tree):
        return Node(union_name, Expressions(*tree))

    def select(self, tree):
        returning_stmt, query_stmt, orderby_stmt, union_stmt = tree
        # evalute order
        dic = {
            "FROM": [],
            "JOIN": [],
            "WHERE": [],
            "GROUPBY": [],
            "HAVING": [],
            "RETURNING": [returning_stmt[1]],
            "ORDERBY": [],
            "WINDOW": [],
            "LIMIT": [],
            "OFFSET": [],
            "UNION": [],
            "INTERSECT": [],
            "EXCEPT": [],
        }

        if query_stmt is None:
            query_stmt = []
        else:
            query_stmt = query_stmt[1]

        for stmt in query_stmt:
            if stmt is not None:
                try:
                    dic[stmt[0]].append(stmt[1])
                except KeyError:
                    raise

        for stmt in orderby_stmt or []:
            dic[stmt[0]].append(stmt[1])

        for stmt in union_stmt or []:
            dic[stmt[0]].append(stmt[1])

        u1 = dic.pop("UNION", None)
        u2 = dic.pop("INTERSECT", None)
        u3 = dic.pop("EXCEPT", None)

        if u1:
            dic.setdefault("unions", Expressions()).append(UnionStatement("UNION", u1))

        if u2:
            dic.setdefault("unions", Expressions()).append(
                UnionStatement("INTERSECT", u2)
            )

        if u3:
            dic.setdefault("unions", Expressions()).append(UnionStatement("EXCEPT", u3))

        for values in dic.values():
            if len(values) > 1:
                raise RuntimeError()

        dic["from_"] = dic.pop("FROM")
        dic["joins"] = dic.pop("JOIN")

        stmt = {**{k.lower(): v[0] for k, v in dic.items() if len(v) == 1}}

        return SelectStatement(**stmt)


class SqlTransformer(SelectTransformer):
    ...


def get_parser(
    start: Literal["start", "value", "stmt", "expr"] = "start",
    cls_transformer=SqlTransformer,
    parser_type: Literal["earley", "lalr"] = "earley",
):
    with open(path + "/grammer2.lark") as grammer:
        parser = Lark(grammer.read(), start=start, parser=parser_type)

        if cls_transformer is None:

            def parse(text: str):
                tree = parser.parse(text)
                return tree

        else:
            transformer = cls_transformer()

            def parse(text: str):
                tree = parser.parse(text)
                result = transformer.transform(tree)
                return result

        return parse
